from videocreation.subtitles import transcript_to_srt, words_to_srt


def _words(texts, start=0.0, dur=0.3, gaps=None):
    gaps = gaps or {}
    out, t = [], start
    for i, w in enumerate(texts):
        t += gaps.get(i, 0.0)
        out.append({"word": w, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    return out


def _cues(srt):
    return [block.split("\n") for block in srt.strip().split("\n\n")]


def test_groups_words_in_short_cues():
    words = _words(["uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove"])
    cues = _cues(words_to_srt(words, max_words=4))
    assert len(cues) == 3
    assert cues[0] == ["1", "00:00:00,000 --> 00:00:01,200", "uno due tre quattro"]
    assert cues[2] == ["3", "00:00:02,400 --> 00:00:02,700", "nove"]


def test_breaks_on_pause():
    words = _words(["ciao", "a", "tutti", "oggi"], gaps={2: 1.0})
    cues = _cues(words_to_srt(words, max_words=4))
    assert [c[2] for c in cues] == ["ciao a", "tutti oggi"]


def test_breaks_on_max_chars():
    words = _words(["straordinariamente", "complicatissimo", "breve"])
    cues = _cues(words_to_srt(words, max_words=4, max_chars=28))
    assert [c[2] for c in cues] == ["straordinariamente", "complicatissimo breve"]


def test_timestamp_format_over_one_hour():
    words = [{"word": "fine", "start": 3725.5, "end": 3726.0}]
    assert "01:02:05,500 --> 01:02:06,000" in words_to_srt(words)


def test_strips_whitespace_and_skips_empty_words():
    words = [
        {"word": " Ciao", "start": 0.0, "end": 0.4},
        {"word": "  ", "start": 0.4, "end": 0.5},
        {"word": "mondo ", "start": 0.5, "end": 0.9},
    ]
    assert _cues(words_to_srt(words))[0][2] == "Ciao mondo"


def test_uses_word_timing_when_words_match_segment():
    result = {
        "words": _words(["a", "b"], start=1.0),
        "segments": [{"start": 0, "end": 9, "text": "a b"}],
    }
    assert _cues(transcript_to_srt(result))[0][1:] == ["00:00:01,000 --> 00:00:01,600", "a b"]


def test_uses_words_without_segments():
    result = {"words": _words(["a", "b"])}
    assert _cues(transcript_to_srt(result))[0][2] == "a b"


def test_keeps_numbers_missing_from_words():
    # Gli allineatori lasciano senza tempi numeri e simboli: VoiceStudio li toglie da `words`.
    result = {
        "segments": [{"start": 0.0, "end": 2.0, "text": " 3 errori da evitare"}],
        "words": [
            {"word": "errori", "start": 0.4, "end": 0.9},
            {"word": "da", "start": 0.9, "end": 1.1},
            {"word": "evitare", "start": 1.1, "end": 1.9},
        ],
    }
    assert _cues(transcript_to_srt(result)) == [
        ["1", "00:00:00,000 --> 00:00:02,000", "3 errori da evitare"]
    ]


def test_mismatch_in_one_segment_keeps_word_timing_in_others():
    result = {
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "ciao a tutti"},
            {"start": 5.0, "end": 6.0, "text": "il 20% in più"},
        ],
        "words": _words(["ciao", "a", "tutti"], start=0.1, dur=0.2)
        + [{"word": "il", "start": 5.0, "end": 5.2}, {"word": "in", "start": 5.5, "end": 5.7},
           {"word": "più", "start": 5.7, "end": 6.0}],
    }
    cues = _cues(transcript_to_srt(result))
    assert cues[0][1:] == ["00:00:00,100 --> 00:00:00,700", "ciao a tutti"]
    assert cues[1][2] == "il 20% in più"
    assert cues[1][1].startswith("00:00:05,000")


def test_falls_back_to_segments():
    result = {"words": [], "segments": [{"start": 0, "end": 2.5, "text": " Ciao a tutti "}]}
    assert _cues(transcript_to_srt(result)) == [
        ["1", "00:00:00,000 --> 00:00:02,500", "Ciao a tutti"]
    ]


def test_empty_transcript():
    assert transcript_to_srt({"text": "", "words": [], "segments": []}) == ""
    assert transcript_to_srt({"text": ""}) == ""


def test_punctuation_difference_keeps_word_timing_and_segment_text():
    result = {
        "segments": [{"start": 0.0, "end": 3.0, "text": "Ciao, a tutti!"}],
        "words": [{"word": "ciao", "start": 0.2, "end": 0.5},
                  {"word": "a", "start": 0.5, "end": 0.6},
                  {"word": "tutti", "start": 0.6, "end": 1.0}],
    }
    assert _cues(transcript_to_srt(result)) == [
        ["1", "00:00:00,200 --> 00:00:01,000", "Ciao, a tutti!"]
    ]
