# from label_characters import label_gui
# from pathlib import Path
# import os
# import regex as re

# TODO:
# [x] Remove the text tagger
# [x] Chunking system:
#     [x] Use token sentence_id, paragraph_id, byte onset/offset to calculate chars
#     [x] Export as JSON
# [x] Audio generation
# [x] Voice tuning / profiles + GUI
# [x] Main menu + GUI
# [x] Merge GUIs
# [x] PDF support (PyMuPDF)
# [x] Standardize file paths and shit, better variable names, commenting, etc.
# [x] Put it all together
# [ ] NOTE TO SELF: threading... ? 🥺  just might increase by ~ 3x meaning realtime for me on CPU babyyy
#                                 👉👈
# [ ] ADDITIONAL NOTE: When installing, python -m spacy download en_core_web_sm
# [ ] ALSO: need libsox

"""
I need a GUI in tkinter that is similar in style to the example below. It's part of a larger project for generating audiobooks using TTS software. Here's what it needs to do:
1. File upload area for importing a book as PDF or txt
2. Title of project input area
3. Toggle for whether or not the audiobook uses multiple voices
4. Button to quit
5a. Button to continue
5b. When the button is pressed, the operation will take a long time. Indicate this to the user (5mins)
"""

# Main menu functions:
# [x] Select from options of what to do
#   [x] Create audiobook
#     [x] Import from text or PDF
#     [x] Multivoice toggle
#     [x] Metadata
#     [x] Voice assignment
#     [x] Chunk generation
#     [x] Continue to "processing"
#   [x] Resume audiobook
#   [x] Create voices
#   [x] Processing
#     [x] Threading
#     [x] GPU / CPU / device selection
#     [x] Logging / debug




# from parse_book import parse 
# parse("LOTM1-2-2.txt", "LOTMA3")
# label_gui("custom/books/tbi_first_try")

# from chunk import generate_chunks, export_chunks

# chunks = generate_chunks("LOTMA3/parsed", {}, multivoice=False, min_length = 5, max_length = 100, passes=2)
# export_chunks(chunks, 'LOTMA3/text/')

# from generate_audio import ModelContainer, VoiceArguments
# import time
# t1 = time.time()
# mc = ModelContainer('cpu')
# t2 = time.time()
# vargs = VoiceArguments(
#     name="Test Voice",
#     reference_path=Path("chatterbox-Audiobook/voice_library/kramer_narration/reference.wav"),
#     exaggeration=0.4,
#     cfg_weight=0.7,
#     temperature=0.7
# )
# t3 = time.time()
# wav = mc.generate("This is a test. How well will this AI perform? Who knows. After all, It's only a test.", args=vargs)
# t4 = time.time()
# import torchaudio as ta
# t5 = time.time()
# ta.save("output.wav", wav, mc.model.sr)
# t6 = time.time()
# print(t2-t1)
# print(t4-t3)
# print(t6-t5)

# from generate_audio import *

# device = Device(device='cpu')
# model = ModelContainer(device)

# generate(model, 'LOTMA3')


# from parse_book import parse

# parse('/Users/davidweir/Documents/Books/tbi/Text/tbi.pdf', 'pdf_test/')



# src = '/Users/davidweir/Documents/Books/tbi/Text/tbi.pdf'
# dest = 'output22.txt'
# import os, pymupdf
# os.system('rm ' + dest)


# ta = ''
# with pymupdf.open(src) as doc:
#     for page in doc:
#         blocks = page.get_text("blocks", sort=True)
#         for x0, y0, x1, y1, txt_block, bno, btype in blocks:
#             clean = txt_block.replace("\n", " ")
#             ta += clean.strip() + "\n"
#         ta.strip('\n')
# with open(dest, "w") as f:
#     f.write(ta.strip())


# from booknlp.booknlp import BookNLP
# from pathlib import Path
# import torch
# import os
# import regex as re
# import unidecode
# import urllib

# # Removes 'position_ids' from a model's state dict and saves the modified model
# def remove_position_ids_and_save(model_file, device, save_path):
#     state_dict = torch.load(model_file, map_location=device)

#     if 'bert.embeddings.position_ids' in state_dict:
#         print(f'Removing "position_ids" from the state dictionary of {model_file}')
#         del state_dict['bert.embeddings.position_ids']

#     torch.save(state_dict, save_path)
#     print(f'Modified state dict saved to {save_path}')

# # Processes model files in model_params, removing 'position_ids' if present
# def process_model_files(model_params, device):
#     updated_params = {}
#     for key, path in model_params.items():
#         # Only process files that are .model files and exist
#         if isinstance(path, str) and os.path.isfile(path) and path.endswith('.model'):
#             save_path = path.replace('.model', '_modified.model')
#             remove_position_ids_and_save(path, device, save_path)
#             updated_params[key] = save_path
#         else:
#             updated_params[key] = path
#     return updated_params

# # Main function to parse a book file and process it with BookNLP
# def parse():
#     user_dir = user_dir = Path.home()
#     model_params = {
#         'pipeline': 'entity,quote,supersense,event,coref',
#         'model': 'custom',
#         'entity_model_path': os.path.join(user_dir, "booknlp_models", "entities_google_bert_uncased_L-6_H-768_A-12-v1.0.model"),
#         'coref_model_path': os.path.join(user_dir, "booknlp_models", "coref_google_bert_uncased_L-12_H-768_A-12-v1.0.model"),
#         'quote_attribution_model_path': os.path.join(user_dir, "booknlp_models", "speaker_google_bert_uncased_L-12_H-768_A-12-v1.0.1.model"),
#         'bert_model_path': os.path.join(user_dir,  ".cache", "huggingface", "hub")
#     }

#     # Select device: CUDA, MPS, or CPU
#     device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')

#     # Process model files to remove position_ids if needed
#     model_params = process_model_files(model_params, device)

#     # booknlp_path = Path(os.path.join(dest_path, "parsed"))

#     # if not booknlp_path.exists():
#     #     booknlp_path.mkdir(parents=True, exist_ok=True)

#     # Run BookNLP processing
#     booknlp = BookNLP('en', model_params)
#     booknlp.process('output22.txt', 'pdf_test', 'book')

# from parse_book import parse

# src = '/Users/davidweir/Documents/Books/tbi/Text/tbi.pdf'
# dest = 'output25.txt'
# import os, pymupdf


# ta = ''
# with pymupdf.open(src) as doc:
#     for page in doc:
#         blocks = page.get_text("blocks", sort=True)
#         for x0, y0, x1, y1, txt_block, bno, btype in blocks:
#             clean = txt_block.replace("\n", " ")
#             ta += clean + "\n\n"
#         if len(ta) > 1 and ta[-2:] == "\n\n":
#             ta = ta[:-2]
# with open(dest, "w") as f:
#     f.write(ta.strip())

# parse('output25.txt', 'pdf_test3')

from pprint import pprint
a = [i for i in range(10)]
b = ["ab" + str(i) + "ba" for i in range(10)]
c = [0.5*i for i in range(10)]

pprint([i for i in zip(a,b,c)])


import tqdm
_original_tqdm = tqdm.tqdm

def tqdm_patched(*args, **kwargs):
    kwargs.setdefault('leave', False)
    return _original_tqdm(*args, **kwargs)

tqdm.tqdm = tqdm_patched

from chatterbox import ChatterboxTTS