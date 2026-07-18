from src.content_extractor import clean_html


def test_clean_static_html_removes_noise():
    html = "<html><title>T</title><body><nav>menu</nav><script>x</script><main>Важный текст услуги</main></body></html>"
    title, text = clean_html(html)
    assert title == "T"
    assert "Важный текст" in text
    assert "menu" not in text
    assert "script" not in text


def test_limits_page_length():
    _, text = clean_html("<main>" + ("a" * 12000) + "</main>")
    assert len(text) == 10000
