import shutil
import pymupdf
from booknlp.booknlp import BookNLP
from pathlib import Path
import torch
import os
import regex as re
import unidecode
import urllib

# Removes 'position_ids' from a model's state dict and saves the modified model
def remove_position_ids_and_save(model_file, device, save_path):
    state_dict = torch.load(model_file, map_location=device)

    if 'bert.embeddings.position_ids' in state_dict:
        print(f'Removing "position_ids" from the state dictionary of {model_file}')
        del state_dict['bert.embeddings.position_ids']

    torch.save(state_dict, save_path)
    print(f'Modified state dict saved to {save_path}')

# Processes model files in model_params, removing 'position_ids' if present
def process_model_files(model_params, device):
    updated_params = {}
    for key, path in model_params.items():
        # Only process files that are .model files and exist
        if isinstance(path, str) and os.path.isfile(path) and path.endswith('.model'):
            save_path = path.replace('.model', '_modified.model')
            remove_position_ids_and_save(path, device, save_path)
            updated_params[key] = save_path
        else:
            updated_params[key] = path
    return updated_params

# Main function to parse a book file and process it with BookNLP
def parse(src_path: os.PathLike, dest_path: os.PathLike):
    src_path = Path(src_path)
    dest_path = Path(dest_path)
    # Create destination directory if it doesn't exist
    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)
    # Check if source file exists and is a file
    if not (src_path.exists() and src_path.is_file()):
        raise ValueError("Source path is not a file or does not exist.")
    

    text_content = ""
    source_text = ""
    is_pdf = False
    sanitized_path = Path(os.path.join(dest_path, "text"))
    # Read and normalize the text content
    if src_path.suffix == '.pdf':
        is_pdf = True
        ta = ''
        with pymupdf.open(src_path) as doc:
            for page in doc:
                blocks = page.get_text("blocks", sort=True)
                for x0, y0, x1, y1, txt_block, bno, btype in blocks:
                    clean = txt_block.replace("\n", " ")
                    ta += clean + "\n\n"
                if len(ta) > 1 and ta[-2:] == "\n\n":
                    ta = ta[:-2]
        ta = ta.strip()
        source_text = src_path
        text_content = unidecode.unidecode(ta)
    else:
        with open(src_path, 'r') as f:
            text_content = f.read()
            source_text = text_content
            text_content = unidecode.unidecode(text_content)
    # Add quotes to the end of lines that lack them.
    text_content = re.sub(r'(^(?:(?:"[^"\n]*")|[^"\n"])*"[^"\n]*$)', lambda r: r.group(0) + "\"", text_content,flags=re.MULTILINE)
    #                      |
    #                      |   This motherfucker took me goddamn forever,
    #                      |   (Like literally 5 hours)
    #                      |
    #                      V
    text_content = re.sub(r'((?: |^)"(?=[^"\n]*? "))(?:([^"\n]*?(?: |\'|"))(")([^"\n]*?)(")((?: |\'|")[^"\n]*?(?R)*))', lambda m: m.group(1) + m.group(2) + "'" + m.group(4) + "'" + m.group(6), text_content, flags=re.MULTILINE)
    text_content = text_content.replace("...", ".").replace("--", ",")
    num_content_lines = len(re.findall(r'^...', text_content, re.MULTILINE))
    num_double_newlines = len(re.findall(r'\n\n^...', text_content, re.MULTILINE))
    ratio = 1
    try:
        ratio = num_double_newlines / num_content_lines
    except:
        pass
    if ratio < .9:
        text_content = text_content.replace("\n", "\n\n")


    if not sanitized_path.exists():
        sanitized_path.mkdir(parents=True, exist_ok=True)
    
    if not is_pdf:
        with open(os.path.join(sanitized_path, "source.txt"), "w") as f:
            f.write(source_text)
    else:
        shutil.copy(source_text, Path(os.path.join(sanitized_path, "source.pdf")))

    with open(os.path.join(sanitized_path, "sanitized.txt"), "w") as f:
        f.write(text_content)

    user_dir = Path.home()

    # Model file names
    entityName="entities_google_bert_uncased_L-6_H-768_A-12-v1.0.model"
    corefName="coref_google_bert_uncased_L-12_H-768_A-12-v1.0.model"
    quoteAttribName="speaker_google_bert_uncased_L-12_H-768_A-12-v1.0.1.model"
    modelPath=Path(os.path.join(user_dir, "booknlp_models"))
    if not modelPath.exists():
        modelPath.mkdir(parents=True,exist_ok=True)
    entityPath=Path(os.path.join(modelPath, entityName))

    # Download entity model if not present
    if not Path(entityPath).is_file():
        print("downloading %s" % entityName)
        urllib.request.urlretrieve("http://people.ischool.berkeley.edu/~dbamman/booknlp_models/%s" % entityName, entityPath)

    # Download coreference model if not present
    coref_model=Path(os.path.join(modelPath, corefName))
    if not Path(coref_model).is_file():
        print("downloading %s" % corefName)
        urllib.request.urlretrieve("http://people.ischool.berkeley.edu/~dbamman/booknlp_models/%s" % corefName, coref_model)

    # Download quote attribution model if not present
    quoteAttribModel=Path(os.path.join(modelPath, quoteAttribName))
    if not Path(quoteAttribModel).is_file():
        print("downloading %s" % quoteAttribName)
        urllib.request.urlretrieve("http://people.ischool.berkeley.edu/~dbamman/booknlp_models/%s" % quoteAttribName, quoteAttribModel)
    
    # Set up model parameters for BookNLP
    model_params = {
        'pipeline': 'entity,quote,supersense,event,coref',
        'model': 'custom',
        'entity_model_path': os.path.join(user_dir, "booknlp_models", "entities_google_bert_uncased_L-6_H-768_A-12-v1.0.model"),
        'coref_model_path': os.path.join(user_dir, "booknlp_models", "coref_google_bert_uncased_L-12_H-768_A-12-v1.0.model"),
        'quote_attribution_model_path': os.path.join(user_dir, "booknlp_models", "speaker_google_bert_uncased_L-12_H-768_A-12-v1.0.1.model"),
        'bert_model_path': os.path.join(user_dir,  ".cache", "huggingface", "hub")
    }

    # Select device: CUDA, MPS, or CPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')

    # Process model files to remove position_ids if needed
    model_params = process_model_files(model_params, device)

    booknlp_path = Path(os.path.join(dest_path, "parsed"))

    if not booknlp_path.exists():
        booknlp_path.mkdir(parents=True, exist_ok=True)

    # Run BookNLP processing
    booknlp = BookNLP('en', model_params)
    booknlp.process(Path(os.path.join(sanitized_path, "sanitized.txt")), booknlp_path, 'book')