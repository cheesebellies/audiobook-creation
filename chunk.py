import json
import statistics
from pathlib import Path
import os
import csv

def import_data(src_path: os.PathLike) -> tuple:
    src_path = Path(src_path) / "parsed"
    quotes_path = src_path / "book.quotes"
    tokens_path = src_path / f"book.tokens"
    if not quotes_path.exists() or not quotes_path.is_file():
        raise ValueError(f"Quotes file {quotes_path} does not exist or is not a file.")
    if not tokens_path.exists() or not tokens_path.is_file():
        raise ValueError(f"Tokens file {tokens_path} does not exist or is not a file.")
    
    def _tsv_to_json(src: os.PathLike) -> dict:
        with open(src, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            return list(reader)
    
    qdata = _tsv_to_json(quotes_path)
    tdata = _tsv_to_json(tokens_path)

    return (tdata, qdata)

def prepare_data(tdata: list, qdata: list, scene_names: dict) -> list:
    data = []
    def _get_char(id: int) -> str:
        a = scene_names.get(id)
        b = scene_names.get(-1)
        return a if a else b if b else 'narrator'
    paragraph_index = -2
    sentence_index = -2
    previous_character = None
    for i, token in enumerate(tdata):
        qde = len(qdata) > 0
        current_character = None
        if qde and (int(qdata[0]['quote_start']) <= i <= int(qdata[0]['quote_end'])):
            current_character = _get_char(int(qdata[0]['char_id']))
        else:
            current_character = _get_char(-1)
        if qde and (i == int(qdata[0]['quote_end'])):
            del qdata [0]
        if current_character != previous_character:
            data.append({'character':current_character,'paragraphs':[[[]]]})
            paragraph_index = token['paragraph_ID']
            sentence_index = token['sentence_ID']
        if paragraph_index != token['paragraph_ID']:
            data[-1]['paragraphs'].append([[]])
            sentence_index = token['sentence_ID']
        if sentence_index != token['sentence_ID']:
            data[-1]['paragraphs'][-1].append([])
        data[-1]['paragraphs'][-1][-1].append(token['word'])
        previous_character = current_character
        paragraph_index = token['paragraph_ID']
        sentence_index = token['sentence_ID']

    return data

class Chunk:
    def __init__(self, data: list):
        self.sentences = data
        self.word_count = sum(len(sentence) for sentence in self.sentences)
    
    def split(self):
        if len(self.sentences) == 1:
            sentence = self.sentences[0]
            mid = len(sentence) // 2
            return (
                Chunk([sentence[:mid]]),
                Chunk([sentence[mid:]])
            )

        mid = self.word_count // 2
        c = 0
        for i in range(len(self.sentences)):
            next_c = c + len(self.sentences[i])
            if next_c >= mid:
                # Decide whether to split before or after this sentence
                if mid - c < next_c - mid:
                    return (
                        Chunk(self.sentences[:i]),
                        Chunk(self.sentences[i:])
                    )
                else:
                    return (
                        Chunk(self.sentences[:i+1]),
                        Chunk(self.sentences[i+1:])
                    )
            c = next_c

        # If we reach here, fallback (shouldn't usually happen)
        return (Chunk([]), self)


    def to_dict(self):
        return self.sentences
    
    def __add__(self, other):
        if isinstance(other, Chunk):
            return Chunk(self.sentences + other.sentences)
        return NotImplemented
    
    def __eq__(self, other):
        if isinstance(other, Chunk):
            return self.word_count == other.word_count
        elif other is int:
            return self.word_count == other
        return NotImplemented
    
    def __lt__(self, other):
        if isinstance(other, Chunk):
            return self.word_count < other.word_count
        elif other is int:
            return self.word_count < other
        return NotImplemented
    
    def __gt__(self, other):
        if isinstance(other, Chunk):
            return self.word_count > other.word_count
        elif other is int:
            return self.word_count > other
        return NotImplemented

def export_chunks(charchunks: list, dest_path: os.PathLike):

    NO_SPACE_AFTER = ['#', '$', '(', '@', '[', '\\', '^', '{', '-', '/', '<', '*']
    NO_SPACE_BEFORE = ['!', ')', ',', '-', '/', '.', ':', ';', '@', '\\', ']', '}', '?', '>', '*']

    def combine(l):
        btr = []
        for i in l:
            if (i in NO_SPACE_BEFORE) or ((len(i) > 1) and ("'" in i)):
                if (len(btr) > 0) and (btr[-1] == ' '):
                    del btr[-1]
            btr.append(i)
            if not (i in NO_SPACE_AFTER):
                btr.append(' ')
        return ''.join(btr).strip(" \n")

    tr = []
    for character in charchunks:
        for chunk in character['chunks']:
            chunk = chunk.to_dict()
            al = [item for sublist in chunk for item in sublist]
            ta = combine(al)
            if ta == "\" \"":
                continue
            tr.append({'character': character['character'], 'text': ta})
        

    with open(os.path.join(dest_path, 'chunks.json'), 'w', encoding='utf-8') as f:
        json.dump(tr, f, ensure_ascii=True, indent=2)

def generate_chunks(src_path: os.PathLike, scene_names: dict, multivoice: bool = True, min_length: int = 5, max_length: int = 100, passes: int = 8):
    """
    Having more context in the TTS prompt usually improves quality, but after around 100 words, it only degrades quality.

    Chunks with fewer than 5 words (or 15 characters) may have artifacts.
    
    This function is meant to split text into chunks with the most context possible without sacrificing quality.

    "Words" in this function, are just tokens like actual words, punctuation, etc.
    """

    if not multivoice:
        scene_names = {}
    charchunks = []
    tdata, qdata = import_data(src_path)
    data = prepare_data(tdata, qdata, scene_names)

    # Stats trackers
    total_chunks = 0
    total_words = 0
    oversize_chunks = 0
    undersize_chunks = 0
    chunk_lengths = []
    chunks_per_character = []

    # Initialize chunks as one per paragraph. Then, loop over each chunk and if it's oversize, split it.
    # If it's undersize, choose the smallest neighbor, and merge into it. Only do this within contiguous
    # regions of text spoken by the same character/narrator.

    for i in data:
        charchunks.append({'character': i['character'], 'chunks': []})
        chunks = []
        for j in i['paragraphs']:
            chunks.append(Chunk(j))

        for passcount in range(passes):
            new_chunks = []
            for chunk in chunks:
                if chunk.word_count > max_length:
                    a, b = chunk.split()
                    new_chunks.append(a)
                    new_chunks.append(b)
                else:
                    new_chunks.append(chunk)
            chunks = new_chunks
            del new_chunks

            if len(chunks) >= 2 and chunks[0].word_count < min_length:
                chunks[1] = chunks[0] + chunks[1]
                del chunks[0]

            if len(chunks) >= 2 and chunks[-1].word_count < min_length:
                chunks[-2] = chunks[-2] + chunks[-1]
                del chunks[-1]

            if len(chunks) >= 3:
                c = 1
                while c < len(chunks) - 1:
                    if chunks[c].word_count < min_length:
                        c1l = chunks[c - 1].word_count
                        c2l = chunks[c + 1].word_count
                        if c1l < c2l:
                            chunks[c - 1] = chunks[c - 1] + chunks[c]
                            del chunks[c]
                        else:
                            chunks[c + 1] = chunks[c] + chunks[c + 1]
                            del chunks[c]
                    else:
                        c += 1
        new_chunks = []
        for chunk in chunks:
            if chunk.word_count > max_length:
                a, b = chunk.split()
                new_chunks.append(a)
                new_chunks.append(b)
            else:
                new_chunks.append(chunk)
        chunks = new_chunks
        del new_chunks


        charchunks[-1]['chunks'] = chunks

        # Per-character stats
        chunks_per_character.append(len(chunks))
        for chunk in chunks:
            wc = chunk.word_count
            chunk_lengths.append(wc)
            total_words += wc
            total_chunks += 1
            if wc > max_length:
                oversize_chunks += 1
            elif wc < min_length:
                undersize_chunks += 1

    # # Save result
    # with open('fres.json', 'w', encoding='utf-8') as f:
    #     def chunks_to_serializable(charchunks):
    #         serializable = []
    #         for c in charchunks:
    #             serializable.append({
    #                 "character": c['character'],
    #                 "chunks": [chunk.to_dict() for chunk in c['chunks']]
    #             })
    #         return serializable

    #     json.dump(chunks_to_serializable(charchunks), f, ensure_ascii=False, indent=2)

    # Final Stats Report
    print("\n=============== Chunking Statistics ===============\n")
    print(f"    Characters processed:           {len(charchunks)}")
    print(f"    Total chunks:                   {total_chunks}")
    print(f"    Total words:                    {total_words}")
    print(f"    Oversize chunks (> {max_length}):        {oversize_chunks}")
    print(f"    Undersize chunks (< {min_length}):         {undersize_chunks}")
    if chunk_lengths:
        print(f"    Average chunk length:           {statistics.mean(chunk_lengths):.2f} words")
        print(f"    Median chunk length:            {statistics.median(chunk_lengths):.2f} words")
        print(f"    Minimum chunk length:           {min(chunk_lengths)} words")
        print(f"    Maximum chunk length:           {max(chunk_lengths)} words")
    print(f"    Average chunks per character:   {statistics.mean(chunks_per_character):.2f}")
    print(f"    Characters with 1 chunk:        {sum(1 for x in chunks_per_character if x == 1)}")
    print(f"    Characters with >10 chunks:     {sum(1 for x in chunks_per_character if x > 10)}")
    print("\n===================================================\n")
    export_chunks(charchunks,src_path / 'text')
