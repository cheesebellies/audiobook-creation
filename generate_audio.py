import json
import os
import sys
from queue import Queue, Empty
from threading import Event, Thread, Lock
from pathlib import Path
import torch
import torchaudio as ta
import gc
import time
import numpy as np
import tqdm
_tqdm = tqdm.tqdm
def tqdmr(*args, **kwargs):
    kwargs['disable'] = True
    return _tqdm(*args, **kwargs)
tqdm.tqdm= tqdmr

from chatterbox import ChatterboxTTS
import perth
from typing import Optional


class NoWatermark(perth.WatermarkerBase):
    def apply_watermark(self, wav: np.ndarray, watermark: Optional[np.ndarray] = None, 
                       sample_rate: int = 44100, **kwargs) -> np.ndarray:
        return wav

    def get_watermark(self, watermarked_wav: np.ndarray, sample_rate: int = 44100,
                     watermark_length: Optional[int] = None, **kwargs) -> np.ndarray:
        length = watermark_length if watermark_length is not None else 32
        return np.random.randint(0, 2, size=length).astype(np.float32)

class SafeEvent(Event):
    def safe_wait(self, exit_case: Event, timeout: float | None = None) -> bool:
        while True:
            assert not exit_case.is_set()
            if self.is_set():
                return True
            elif timeout:
                if timeout <= 0.0:
                    return False
                if timeout <= 0.1:
                    timeout = 0.0
                    self.wait(timeout=timeout)
                else:
                    self.wait(timeout=0.1)
            else:
                time.sleep(0.1)

class Device:
    def __init__(self, device: str | None = None):
        if device and device == "default":
            device = 'cpu'
        if device:
            self.device = device.lower()
        elif torch.cuda.is_available():
            self.device = 'cuda'
        elif torch.backends.mps.is_available():
            self.device = 'mps'
        else:
            self.device = 'cpu'
        if self.device == "mps":
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    
    def cleanup(self):
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        if self.device == "mps":
            torch.mps.empty_cache()
            torch.mps.synchronize()
    
    def __str__(self):
        return self.device
        
class VoiceArguments:
    def __init__(self, name: str, reference_path: os.PathLike | None = None, exaggeration: float = 0.4, cfg_weight: float = 0.7, temperature: float = 0.7, pitch: float = 0.0):
        self.name = name
        self.reference_path = Path(reference_path) if reference_path else None
        self.exaggeration = exaggeration
        self.cfg_weight = cfg_weight
        self.temperature = temperature
        self.pitch = pitch
    
    @staticmethod
    def get_default() -> "VoiceArguments":
        return VoiceArguments(
                name="Default Voice",
                reference_path=None,
                exaggeration=0.4,
                cfg_weight=0.7,
                temperature=0.7,
                pitch=0.0
            )

    @staticmethod
    def from_file(file: os.PathLike) -> "VoiceArguments":
        s = Path(file)
        if not (s.exists() and s.is_file()):
            raise ValueError("File does not exist or is a directory.")
        with open(file, 'r') as f:
            i = json.load(f)
            return VoiceArguments(
                name=i.get("name", "Voice"),
                reference_path=i.get("reference_path", None),
                exaggeration=i.get("exaggeration", 0.4),
                cfg_weight=i.get("cfg_weight", 0.7),
                temperature=i.get("temperature", 0.7),
                pitch=i.get("pitch", 0.0)
            )

class ModelContainer:
    def __init__(self, device: Device):
        self.model = ChatterboxTTS.from_pretrained(str(device))
        self.model.watermarker = NoWatermark()
        self.sr = self.model.sr
        self.device = device
        self.reloading = False


    def generate(self, text: str, args: VoiceArguments | None = None, **optional_params) -> torch.Tensor:
        if not args:
            res = self.model.generate(text, **optional_params)
        res = self.model.generate(
            text,
            audio_prompt_path=args.reference_path,
            exaggeration=args.exaggeration,
            cfg_weight=args.cfg_weight,
            temperature=args.temperature,
            **optional_params
        )
        if args.pitch != 0:
            r = self.pitch_shift(res, args.pitch)
            return r
        return res
    
    def pitch_shift(self, audio: torch.Tensor, shift: float):
        if shift == 0:
            return audio
        try:
            sr = self.model.sr
            effects = [
                ['pitch', f'{int(shift * 100)}'],
                ['rate', f'{sr}']
            ]
            waveform_shifted, _ = ta.sox_effects.apply_effects_tensor(
                audio, sr, effects
            )
            return waveform_shifted
        except Exception as e:
            print(e)
            return audio

    def reload_model(self):
        self.reloading = True
        del self.model
        self.device.cleanup()
        self.model = ChatterboxTTS.from_pretrained(str(self.device))
        self.model.watermarker = NoWatermark()
        self.device.cleanup()
        self.reloading = False
    
    def cleanup(self):
        # Stolen shamelessly from https://github.com/kariedo/audiobook-chatterbox-tts-scripts
        try:
            # Clear T3 model KV-cache if it exists
            if hasattr(self.model, 't3') and hasattr(self.model.t3, 'patched_model'):
                # Clear any cached past_key_values or internal state
                if hasattr(self.model.t3.patched_model, 'clear_cache'):
                    self.model.t3.patched_model.clear_cache()
                
                # Force clear any transformer internal caches
                if hasattr(self.model.t3.patched_model, 'tfmr'):
                    tfmr = self.model.t3.patched_model.tfmr
                    # Clear position embeddings cache if it exists
                    if hasattr(tfmr, '_position_embeddings_cache'):
                        tfmr._position_embeddings_cache.clear()
                    # Clear any attention caches
                    for layer in getattr(tfmr, 'layers', []):
                        if hasattr(layer, 'self_attn') and hasattr(layer.self_attn, 'past_key_value'):
                            layer.self_attn.past_key_value = None
            
            # Clear S3Gen flow cache if it exists
            if hasattr(self.model, 's3gen'):
                s3gen = self.model.s3gen
                # Clear conditional flow matching caches
                if hasattr(s3gen, 'cond_cfm') and hasattr(s3gen.cond_cfm, 'flow_cache'):
                    # Reset flow cache to empty state
                    if hasattr(s3gen.cond_cfm, 'reset_cache'):
                        s3gen.cond_cfm.reset_cache()
                    elif hasattr(s3gen.cond_cfm, 'flow_cache'):
                        # Manually clear the flow cache
                        s3gen.cond_cfm.flow_cache = torch.zeros_like(s3gen.cond_cfm.flow_cache[:, :, :0])
                
                # Clear LRU resampler cache occasionally
                if hasattr(s3gen, 'get_resampler') and hasattr(s3gen.get_resampler, 'cache_clear'):
                    s3gen.get_resampler.cache_clear()
            
            # Clear any other potential caches
            if hasattr(self.model, 'clear_caches'):
                self.model.clear_caches()
                
        except Exception as e:
            print("Could not cleanup model: " + str(e))

class Generate:

    def __init__(self, device: Device, src_path: os.PathLike, voices_path: os.PathLike | None, max_workers: int = 1, quit_event = None):

        self.src_path = Path(src_path)
        self.voices_path = Path(voices_path) if voices_path else Path('voices')
        
        self.resetting = SafeEvent()
        self.inv_resetting = SafeEvent()
        self.inv_resetting.set()
        self.threads_complete = [SafeEvent() for i in range(max_workers)]
        for i in self.threads_complete:
            i.set()

        self.max_workers = max_workers
        self.quit_event = quit_event
        self.model = ModelContainer(device)

        self.default_voice = VoiceArguments.get_default()

        # Stats tracking
        self.stats_lock = Lock()
        self.completed_chunks = 0
        self.failed_chunks = 0
        self.start_time = None
        self.last_update_time = None
        
        # Sliding window for ETA calculation (last ~100 chunks)
        self.window_size = 100
        self.recent_chunks = []  # List of (timestamp, chunk_duration) tuples

        self._load_data()
    
    def reset_model(self):
        if self.resetting.is_set():
            self.inv_resetting.safe_wait(self.quit_event)
            return
        self.inv_resetting.clear()
        self.resetting.set()
        for thread_complete in self.threads_complete:
            thread_complete.safe_wait(self.quit_event,timeout=300)
        self.model.reload_model()
        self.resetting.clear()
        self.inv_resetting.set()

    def generate(self):
        self.start_time = time.time()
        self.last_update_time = self.start_time
        
        for chunk, index in zip(self.chunks, self.indices):
            if self.quit_event.is_set():
                self.model.device.cleanup()
                print("Generation exited safely.")
                sys.exit(0)
            stats = self._generate_chunk(chunk, index, 0)
            if stats:
                self._print_stats(stats)

    def generate_threaded(self):
        self.start_time = time.time()
        self.last_update_time = self.start_time
        
        process_queue = Queue(self.total_chunk_len)
        # List of tuples that contain _generate_chunk arguments
        for chunk, index in zip(self.chunks, self.indices):
            process_queue.put((chunk, index))
        
        def _worker(queue: Queue, thread_index: int):
            while not self.quit_event.is_set():
                chunk = None
                index = None
                try:
                    chunk, index = queue.get(block=False)
                except Empty:
                    break
                try:
                    stats = self._generate_chunk(chunk, index, thread_index)
                except Exception as e:
                    stats = {"error": str(e), "index": index, "thread_index": thread_index}
                if stats:
                    self._print_stats(stats)
                queue.task_done()
            self.model.device.cleanup()
        
        threads = []

        for thread_index in range(self.max_workers):
            t = Thread(target=_worker, args=(process_queue, thread_index))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()

        if self.quit_event.is_set():
            self.model.device.cleanup()
            print("Generation exited safely.")
            sys.exit(0)
            

    def _generate_chunk(self, chunk: dict, index: int, thread_index: int):
        if self.quit_event.is_set():
            return None
        chunk_start_time = time.time()
        audio = None
        retries_used = 0
        
        for retry in range(3):
            try:
                self.inv_resetting.safe_wait(self.quit_event)
                self.threads_complete[thread_index].clear()
                wav = self.model.generate(chunk['text'], args=self.voices.get(chunk['character'], self.default_voice))
                self.threads_complete[thread_index].set()
                audio = wav.squeeze(0).cpu().numpy()
                break
            except AssertionError:
                return None
            except RecursionError as e:
                print(f"RecursionError generating chunk {str(index)}: {e}")
                retries_used = retry + 1
                try:
                    self.reset_model()
                except:
                    return {"error": f"Model reset failed after RecursionError: {e}", "index": index, "thread_index": thread_index}
            except Exception as e:
                print(f"Error generating chunk {str(index)}: {e}")
                retries_used = retry + 1
                if retry == 2:
                    try:
                        self.reset_model()
                    except:
                        return {"error": f"Generation failed after 3 retries: {e}", "index": index, "thread_index": thread_index}
            self.model.cleanup()
            self.model.device.cleanup()
        
        if audio is None:
            return {"error": "Audio generation failed after retries", "index": index, "thread_index": thread_index}
        
        # Save audio file
        silence = np.zeros(int(0.2*self.model.sr), dtype=np.float32)
        audio = np.concatenate([audio,silence])
        ta.save(os.path.join(self.dest_path, f"chunk_{index:05d}.wav"),torch.from_numpy(audio).unsqueeze(0), self.model.sr)
        
        # Calculate stats
        chunk_duration = time.time() - chunk_start_time
        audio_duration = len(audio) / self.model.sr
        text_length = len(chunk['text'])
        character = chunk.get('character', 'unknown')
        
        # Cleanup
        wav = None
        audio = None
        silence = None
        self.model.device.cleanup()
        
        return {
            "success": True,
            "index": index,
            "thread_index": thread_index,
            "chunk_duration": chunk_duration,
            "audio_duration": audio_duration,
            "text_length": text_length,
            "character": character,
            "retries_used": retries_used
        }

    def _print_stats(self, stats: dict):
        with self.stats_lock:
            current_time = time.time()
            
            if "error" in stats:
                self.failed_chunks += 1
                print(f"ERROR - Chunk {stats['index']}: {stats['error']}")
                return
            
            if stats.get("success"):
                self.completed_chunks += 1
                
                # Update sliding window for recent performance
                self.recent_chunks.append((current_time, stats["chunk_duration"]))
                if len(self.recent_chunks) > self.window_size:
                    self.recent_chunks.pop(0)
                
                # Calculate progress
                total_processed = self.completed_chunks + self.failed_chunks
                total_remaining = len(self.chunks) - total_processed
                progress_pct = (total_processed / len(self.chunks)) * 100
                
                # Calculate timing stats using sliding window
                if len(self.recent_chunks) >= 2:
                    # Use time span of recent chunks for rate calculation
                    window_start_time = self.recent_chunks[0][0]
                    window_duration = current_time - window_start_time
                    window_chunks = len(self.recent_chunks)
                    
                    chunks_per_second = window_chunks / window_duration if window_duration > 0 else 0
                    avg_chunk_time = sum(duration for _, duration in self.recent_chunks) / len(self.recent_chunks)
                else:
                    # Fallback to overall stats for first few chunks
                    elapsed_time = current_time - self.start_time
                    chunks_per_second = total_processed / elapsed_time if elapsed_time > 0 else 0
                    avg_chunk_time = elapsed_time / total_processed if total_processed > 0 else 0
                
                eta_seconds = total_remaining / chunks_per_second if chunks_per_second > 0 else 0
                
                # Format ETA
                if eta_seconds < 60:
                    eta_str = f"{eta_seconds:.0f}s"
                elif eta_seconds < 3600:
                    eta_str = f"{eta_seconds/60:.0f}m {eta_seconds%60:.0f}s"
                elif eta_seconds < 86400:  # Less than 24 hours
                    eta_str = f"{eta_seconds/3600:.0f}h {(eta_seconds%3600)/60:.0f}m"
                else:  # 24 hours or more
                    days = int(eta_seconds // 86400)
                    remaining_seconds = eta_seconds % 86400
                    hours = int(remaining_seconds // 3600)
                    minutes = int((remaining_seconds % 3600) // 60)
                    eta_str = f"{days}d {hours}h {minutes}m"
                
                # Calculate real-time factor (how much faster than real-time)
                individual_rtf = stats["audio_duration"] / stats["chunk_duration"] if stats["chunk_duration"] > 0 else 0
                effective_rtf = individual_rtf * self.max_workers if self.max_workers > 1 else individual_rtf
                
                # Thread info for threaded generation
                thread_info = f" [T{stats['thread_index']}]" if self.max_workers > 1 else ""
                
                # Retry info
                retry_info = f" ({stats['retries_used']} retries)" if stats["retries_used"] > 0 else ""
                
                # Print progress update
                if self.max_workers > 1:
                    rtf_display = f"RTF: {individual_rtf:.2f}x (effective: {effective_rtf:.2f}x)"
                else:
                    rtf_display = f"RTF: {effective_rtf:.2f}x"
                
                print(f"Chunk {stats['index']:05d}/{len(self.chunks):05d}{thread_info} - "
                      f"{progress_pct:.1f}% - "
                      f"Character: {stats['character'][:15]} - "
                      f"Duration: {stats['chunk_duration']:.2f}s - "
                      f"{rtf_display} - "
                      f"Rate: {chunks_per_second:.2f} chunks/s - "
                      f"ETA: {eta_str}"
                      f"{retry_info}")
                
                # Print summary every 10 chunks or when complete
                if total_processed % 10 == 0 or total_processed == len(self.chunks):
                    success_rate = (self.completed_chunks / total_processed) * 100
                    overall_elapsed = current_time - self.start_time
                    overall_avg_time = overall_elapsed / total_processed
                    
                    window_info = f" (based on last {len(self.recent_chunks)} chunks)" if len(self.recent_chunks) >= 10 else ""
                    
                    print(f"SUMMARY: {total_processed+self.completed_chunks}/{len(self.chunks)} chunks processed - "
                          f"Success rate: {success_rate:.1f}% - "
                          f"Recent avg: {avg_chunk_time:.2f}s{window_info} - "
                          f"Overall avg: {overall_avg_time:.2f}s - "
                          f"Total elapsed: {overall_elapsed/60:.1f}m")
                
                self.last_update_time = current_time

    @staticmethod
    def generate_sample(text: str, voice: VoiceArguments):
        print("Generating sample \"" + text + "\"\nVoice: \"" + str(voice.name) + "\"")
        device = Device(device='cpu')
        model = ModelContainer(device)
        wav = model.generate(text, voice)
        audio = wav.squeeze(0).cpu().numpy()
        audio_int16 = (audio * 32767).astype(np.int16)
        sr = model.model.sr
        del wav, audio, model
        device.cleanup()
        return (audio_int16, sr)

    def _load_data(self):
        if not (self.src_path.exists() and self.src_path.is_dir()):
            raise ValueError('Source path does not exist or is a file.')
        chunks = []
        src_chunks = Path(os.path.join(self.src_path, 'text', 'chunks.json'))
        if not (src_chunks.exists() and src_chunks.is_file()):
            raise ValueError('Chunks file does not exist. Please generate it first.')
        if self.voices_path and (Path(self.voices_path).is_file() or not Path(self.voices_path).exists()):
            raise ValueError('Voices path is not a directory or does not exist.')
        
        with open(src_chunks, 'r') as f:
            chunks = json.load(f)
        total_chunk_len = len(chunks)
        indices = []
        if not chunks:
            raise ValueError('No chunks found in the file.')
        self.dest_path = Path(os.path.join(self.src_path, 'audio'))
        if self.dest_path.exists() and not self.dest_path.is_dir():
            raise ValueError('Destination path exists but is not a directory.')
        if not self.dest_path.exists():
            self.dest_path.mkdir(parents=True, exist_ok=True)
        
        generated_indices = [int(f.stem.split('_')[-1]) for f in self.dest_path.glob('chunk_*.wav')]
        indices = [i for i in range(total_chunk_len) if i not in generated_indices]
        chunks = [i for j, i in enumerate(chunks) if j not in generated_indices]
        voices = {}

        if self.voices_path:
            for i in os.listdir(self.voices_path):
                voice = VoiceArguments.from_file(os.path.join(self.voices_path, i, 'settings.json'))
                voices[str(i)] = voice
        if len(voices) < 1:
            voices = {'narrator': self.default_voice}
        
        self.chunks = chunks
        self.voices = voices
        self.indices = indices
        self.total_chunk_len = total_chunk_len
