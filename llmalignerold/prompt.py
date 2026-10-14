from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def clean_text(text:str) -> str:
    return text.strip().split("\n")[0]


def build_prompt(data, item_id, example_ids, corpus1:str, corpus2:str, guidelines:str="") -> ChatPromptTemplate:
    human_message = f"""
        You need to align words in two versions of the same text: '{corpus1}' and '{corpus2}'.
        You will be given the two texts in CoNLL-U format.
        You can use the actual words, lemmas, POS tags, and dependency relations to help you align the words.
    """

    if guidelines:
        human_message += f"""
        Here are some guidelines to help you with the alignment:
        {guidelines}
        """
        
    human_message += f"""
        These are examples of the CoNLL-U input that you need to align:
    """
    for example_id in example_ids:
        item = data[example_id]
        human_message += "\n#--- Example ---\n"
        corpus1_text = item[corpus1]["conllu"]
        corpus2_text = item[corpus2]["conllu"]
        human_message += f"{corpus1}:\n{corpus1_text}\n---\n"
        human_message += f"{corpus2}:\n{corpus2_text}\n---\n"

    human_message += f"""
        Your task is to produce an alignment in URGARIT format.
        For each link of aligned words, write the ID of the word in {corpus1}, followed by a hyphen, followed by the ID of the word in {corpus2}.
        Then you provide a confidence value, with 'S' for sure alignments and 'P' for probable alignments.
        Examples:
        - `3-5S`
        - `12-18P`
        The alignment string is a **space-separated list** of alignment links.
        **Order does not matter**; the alignment is a set, not a sequence.
        By default, align in the order of the first corpus '{corpus1}'.
        If a word in one corpus has no alignment in the other corpus, simply omit it from the alignment.
        Do not include any words that are not aligned.
        Only align words that you are reasonably confident about.
        UGARIT supports:
        - one-to-one (1–1)
        - one-to-many (1–N)
        - many-to-one (N–1)
        - many-to-many (N–N)

        Example: 
        1-2S 3-4P 5-6S 7-8S 9-10P

        Your first line of output should be the alignment string only and then a newline.
        No other text should be output before or after the alignment string. Just stop.
        Make sure you do not get any of the alignment wrong, otherwise you will be punished.

        Here are the texts for you to align with 100% accuracy.
    """
    item = data[item_id]
    corpus1_text = item[corpus1]["conllu"]
    corpus2_text = item[corpus2]["conllu"]
    human_message += f"{corpus1}:\n{corpus1_text}\n---\n"
    human_message += f"{corpus2}:\n{corpus2_text}\n---\n"

    human_message = human_message.replace("\n        ", "\n").strip()
    messages = [
        ("system", f"You are a computational linguist"),
        ("user", human_message),
    ]
    return ChatPromptTemplate.from_messages(messages=messages)


def build_chain(llm, data, item_id, example_ids, corpus1:str, corpus2:str, guidelines:str=""):
    prompt = build_prompt(data, item_id, example_ids, corpus1=corpus1, corpus2=corpus2, guidelines=guidelines)
    chain = prompt | llm | StrOutputParser() | clean_text
    return chain
