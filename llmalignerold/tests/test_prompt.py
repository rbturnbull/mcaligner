from langchain_core.runnables import RunnableLambda

from llmaligner.prompt import clean_text, build_prompt, build_chain


def _dummy_data():
    return {
        "ex1": {
            "c1": {"conllu": "1\tHello\n"},
            "c2": {"conllu": "1\tBonjour\n"},
        },
        "ex2": {
            "c1": {"conllu": "1\tGoodbye\n"},
            "c2": {"conllu": "1\tAu revoir\n"},
        },
        "item": {
            "c1": {"conllu": "1\tYes\n"},
            "c2": {"conllu": "1\tOui\n"},
        },
    }


def test_clean_text_strips_and_first_line():
    assert clean_text("  hi\nthere\n") == "hi"


def test_build_prompt_includes_examples_and_item():
    data = _dummy_data()
    prompt = build_prompt(
        data,
        item_id="item",
        example_ids=["ex1", "ex2"],
        corpus1="c1",
        corpus2="c2",
        guidelines="Be careful.",
    )

    formatted = prompt.format_messages()[1].content

    assert "Here are some guidelines" in formatted
    assert "Be careful." in formatted
    assert "#--- Example ---" in formatted
    assert "c1:\n1\tHello" in formatted
    assert "c2:\n1\tBonjour" in formatted
    assert "c1:\n1\tGoodbye" in formatted
    assert "c2:\n1\tAu revoir" in formatted
    assert "Here are the texts for you to align" in formatted
    assert "c1:\n1\tYes" in formatted
    assert "c2:\n1\tOui" in formatted


def test_build_prompt_without_guidelines_omits_section():
    data = _dummy_data()
    prompt = build_prompt(
        data,
        item_id="item",
        example_ids=["ex1"],
        corpus1="c1",
        corpus2="c2",
        guidelines="",
    )

    formatted = prompt.format_messages()[1].content
    assert "Here are some guidelines" not in formatted


def test_build_chain_runs_through_clean_text():
    data = _dummy_data()
    llm = RunnableLambda(lambda _: "align\nextra")
    chain = build_chain(
        llm,
        data,
        item_id="item",
        example_ids=["ex1"],
        corpus1="c1",
        corpus2="c2",
        guidelines="",
    )

    assert chain.invoke({}) == "align"
