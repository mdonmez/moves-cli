"""
Test the REAL problem: 14 -> 12 intervention

When supervisor moves from slide 14 to slide 12:
- Slide 14 chunks ARE in the candidate list (because 14 - 2 = 12)
- System may want to go back to slide 14!

This is the actual problem scenario.
"""

from collections import Counter
from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.models import Section, SimilarityResult


def create_sections() -> list[Section]:
    """Create test sections."""
    return [
        Section(
            content="acilis konusmasi etkinlige hosgeldiniz bugun sizlerle paylasim",
            section_index=1,
        ),
        Section(
            content="gundem sirket vizyonu urun tanitimi pazar analizi finansal durum",
            section_index=2,
        ),
        Section(
            content="sirket vizyonumuz teknoloji sektorunde lider olmak inovasyon odakli",
            section_index=3,
        ),
        Section(
            content="urun tanitimi yeni platformumuz bulut tabanli mimari mikroservis",
            section_index=4,
        ),
        Section(
            content="platform ozellikleri yapay zeka entegrasyonu dogal dil isleme",
            section_index=5,
        ),
        Section(
            content="teknik altyapi kubernetes docker konteyner orkestrasyonu yuk dengeleme",
            section_index=6,
        ),
        Section(
            content="guvenlik standartlari sifir guven mimarisi veri sifreleme erisim",
            section_index=7,
        ),
        Section(
            content="pazar analizi rekabet durumu pazar payi hedefler buyume stratejisi",
            section_index=8,
        ),
        Section(
            content="musterilerimiz kurumsal segment kucuk isletmeler bireysel kullanicilar gelir",
            section_index=9,
        ),
        Section(
            content="basari hikayeleri referanslarimiz buyuk firmalar olumlu geri bildirimler",
            section_index=10,
        ),
        Section(
            content="gecmis donem performansi onceki yil gelir buyume kar marji",
            section_index=11,
        ),
        # SLIDE 12 - Where supervisor moves TO
        Section(
            content="finansal projeksiyonlar gelecek yil hedefleri yatirim planlari butce tahsisi",
            section_index=12,
        ),
        Section(
            content="yol haritasi urun gelistirme yeni ozellikler beta surum lansman",
            section_index=13,
        ),
        # SLIDE 14 - Where we were BEFORE intervention
        Section(
            content="sonuc olarak urunumuz mukemmel kalitede musteri memnuniyeti en onemli onceliktir",
            section_index=14,
        ),
        Section(
            content="sorular varsa lutfen sorun tesekkurler katildiginiz icin iyi gunler",
            section_index=15,
        ),
    ]


def analyze(
    results: list[SimilarityResult], threshold: float = 0.05
) -> tuple[bool, int | None, str]:
    if len(results) < 2:
        s = results[0].chunk.source_sections[-1].section_index
        return True, s, f"Single result -> {s}"

    s1 = results[0].chunk.source_sections[-1].section_index
    s2 = results[1].chunk.source_sections[-1].section_index
    gap = results[0].score - results[1].score

    if s1 == s2:
        return True, s1, f"CONSISTENT: Both -> Slide {s1}"
    if gap >= threshold:
        return True, s1, f"CONSISTENT: Slide {s1} leads by {gap * 100:.1f}%"
    return False, None, f"INCONSISTENT: {s1} vs {s2}, gap={gap * 100:.1f}%"


def print_results(results: list[SimilarityResult], n: int = 8) -> None:
    print(f"\n{'#':<3} {'Target':<8} {'Score':<8} {'Sources':<12} {'Content'}")
    print("-" * 80)
    for i, r in enumerate(results[:n], 1):
        sources = [s.section_index for s in r.chunk.source_sections]
        target = sources[-1]
        print(
            f"{i:<3} {target:<8} {r.score * 100:.1f}%    {str(sources):<12} {r.chunk.partial_content[:35]}..."
        )


def main():
    print("=" * 80)
    print("PROBLEM SCENARIO: SLIDE 14 -> SLIDE 12 INTERVENTION")
    print("=" * 80)

    sections = create_sections()
    chunks = chunk_producer.generate_chunks(sections, window_size=12)
    calculator = SimilarityCalculator(chunks)
    candidate_gen = chunk_producer.CandidateChunkGenerator(chunks)

    print(f"\n[INFO] {len(sections)} slides, {len(chunks)} chunks")

    # =========================================================================
    # VERIFY: Slide 14 chunks ARE in candidates when on slide 12
    # =========================================================================
    print("\n" + "=" * 80)
    print("VERIFICATION: What chunks are candidates when current = slide 12?")
    print("=" * 80)

    current = sections[11]  # Slide 12
    candidates = candidate_gen.get_candidate_chunks(current)

    target_counts = Counter(c.source_sections[-1].section_index for c in candidates)
    print(f"\n[CANDIDATES] Total: {len(candidates)}")
    print("[BY TARGET SLIDE]:")
    for slide, count in sorted(target_counts.items()):
        marker = " <-- SLIDE 14!" if slide == 14 else ""
        print(f"  Slide {slide}: {count} chunks{marker}")

    slide_14_in_candidates = 14 in target_counts
    print(f"\n[CRITICAL] Slide 14 chunks in candidates: {slide_14_in_candidates}")
    if slide_14_in_candidates:
        print("  *** THIS IS THE PROBLEM! ***")
        print(
            "  When supervisor moves from 14 to 12, slide 14 chunks are still candidates!"
        )

    # =========================================================================
    # SCENARIO: Supervisor moved from 14 to 12, buffer has slide 14 words
    # =========================================================================
    print("\n" + "=" * 80)
    print("THE PROBLEM SCENARIO")
    print("-" * 80)
    print("  1. Speaker was on slide 14, %98-100 confidence")
    print("  2. Supervisor manually moved to slide 12 (2 slides back)")
    print("  3. Buffer still has 10 words from slide 14, 2 words from slide 12")
    print("  4. System compares with candidates (which INCLUDE slide 14 chunks!)")
    print("=" * 80)

    current = sections[11]  # Slide 12 (supervisor moved here)

    # Buffer: 10 words from slide 14, 2 words from slide 12
    # Slide 14: "sonuc olarak urunumuz mukemmel kalitede musteri memnuniyeti en onemli onceliktir"
    # Slide 12: "finansal projeksiyonlar"
    input_mixed = "olarak urunumuz mukemmel kalitede musteri memnuniyeti en onemli onceliktir finansal projeksiyonlar"

    print(f'\n[INPUT] "{input_mixed}"')
    print(f"[CURRENT POSITION] Slide {current.section_index} (set by supervisor)")
    print(f"[BUFFER COMPOSITION] ~10 words from slide 14, ~2 words from slide 12")

    candidates = candidate_gen.get_candidate_chunks(current)
    results = calculator.compare(input_mixed, candidates)
    print_results(results)

    ok, target, msg = analyze(results)
    print(f"\n[ANALYSIS] {msg}")
    print(f"[DECISION] {'NAVIGATE -> Slide ' + str(target) if ok else 'WAIT'}")

    # Check what happened
    top_target = results[0].chunk.source_sections[-1].section_index
    if top_target == 14:
        print("\n" + "*" * 80)
        print("*** PROBLEM CONFIRMED! ***")
        print("System wants to go to slide 14, overriding supervisor's decision!")
        print("*" * 80)
    elif top_target == 12:
        print("\n[OK] System correctly stays on slide 12")
    else:
        print(f"\n[UNEXPECTED] System wants slide {top_target}")

    # =========================================================================
    # What if buffer has MORE slide 14 words?
    # =========================================================================
    print("\n" + "=" * 80)
    print("WORSE CASE: Buffer is 11 words from slide 14, 1 word from slide 12")
    print("=" * 80)

    # Almost all words from slide 14
    input_worse = "sonuc olarak urunumuz mukemmel kalitede musteri memnuniyeti en onemli onceliktir finansal"

    print(f'\n[INPUT] "{input_worse}"')

    results = calculator.compare(input_worse, candidates)
    print_results(results)

    ok, target, msg = analyze(results)
    print(f"\n[ANALYSIS] {msg}")
    print(f"[DECISION] {'NAVIGATE -> Slide ' + str(target) if ok else 'WAIT'}")

    top_target = results[0].chunk.source_sections[-1].section_index
    if top_target == 14:
        print("\n*** PROBLEM! System wants slide 14! ***")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("""
    CandidateChunkGenerator does NOT solve the problem!
    
    It only filters DISTANT slides (e.g., slide 11 when on slide 14).
    But within the range (current +3 / -2), ALL chunks are candidates.
    
    When supervisor moves:
    - From 14 to 12: Slide 14 chunks ARE candidates (14 - 2 = 12)
    - From 14 to 13: Slide 14 chunks ARE candidates (14 - 2 = 12 <= 13)
    
    The problem EXISTS for any intervention within ±2/+3 slides!
    """)


if __name__ == "__main__":
    import io, sys
    from pathlib import Path

    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    main()
    sys.stdout = old

    text = buf.getvalue()
    Path(__file__).with_suffix(".txt").write_text(text, encoding="utf-8")
    print(text)
