"""
Realistic test for manual intervention problem.

This test creates a scenario where:
1. Slide 14 and Slide 11 have OVERLAPPING content (transition chunks exist)
2. When supervisor moves from 14 to 11, transition chunks may cause issues

Run with: uv run python tests/test_realistic_intervention.py
"""

from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.models import Section, SimilarityResult


def create_realistic_sections() -> list[Section]:
    """
    Create sections with some overlapping words to simulate real presentations
    where speakers might reference earlier content.
    """
    return [
        Section(
            content="acilis konusmasi etkinlige hosgeldiniz bugun sizlerle onemli konular paylasacagiz",
            section_index=1,
        ),
        Section(
            content="gundem sirket vizyonu urun tanitimi pazar analizi finansal projeksiyonlar",
            section_index=2,
        ),
        Section(
            content="sirket vizyonumuz teknoloji sektorunde lider olmak inovasyon odakli buyume",
            section_index=3,
        ),
        Section(
            content="urun tanitimi yeni platformumuz bulut tabanli mimari mikroservis yapisi",
            section_index=4,
        ),
        Section(
            content="platform ozellikleri yapay zeka entegrasyonu dogal dil isleme goruntuiseme",
            section_index=5,
        ),
        Section(
            content="teknik altyapi kubernetes docker konteyner orkestrasyonu yuk dengeleme",
            section_index=6,
        ),
        Section(
            content="guvenlik standartlari sifir guven mimarisi veri sifreleme erisim kontrolu",
            section_index=7,
        ),
        Section(
            content="pazar analizi rekabet durumu pazar payi hedefler buyume stratejisi",
            section_index=8,
        ),
        Section(
            content="musterilerimiz kurumsal segment kucuk isletmeler bireysel kullanicilar",
            section_index=9,
        ),
        Section(
            content="basari hikayeleri musterilerimiz urunumuzu kullanan firmalar geri bildirimler",
            section_index=10,
        ),
        # SLIDE 11 - Has some unique content
        Section(
            content="gecmis donem performansi onceki yil sonuclari buyume oranlari kar marji",
            section_index=11,
        ),
        Section(
            content="finansal projeksiyonlar gelecek yil hedefleri yatirim planlari butce",
            section_index=12,
        ),
        Section(
            content="yol haritasi urun gelistirme plani yeni ozellikler lansman tarihleri",
            section_index=13,
        ),
        # SLIDE 14 - Contains words that are UNIQUE to this slide
        Section(
            content="sonuc olarak urun mukemmel kalitede uretildi musteri memnuniyeti oncelik",
            section_index=14,
        ),
        Section(
            content="sorular varsa lutfen sorun tesekkurler katildiginiz icin iyi gunler",
            section_index=15,
        ),
    ]


def analyze_consistency(
    results: list[SimilarityResult], score_gap_threshold: float = 0.05
) -> tuple[bool, int | None, str]:
    """Analyze top 2 results for consistency."""
    if len(results) < 2:
        section = results[0].chunk.source_sections[-1].section_index
        return True, section, f"CONSISTENT: Single result -> Slide {section}"

    top_1 = results[0]
    top_2 = results[1]

    section_1 = top_1.chunk.source_sections[-1].section_index
    section_2 = top_2.chunk.source_sections[-1].section_index

    score_gap = top_1.score - top_2.score

    if section_1 == section_2:
        return (
            True,
            section_1,
            (
                f"CONSISTENT: Top 2 -> Slide {section_1} "
                f"({top_1.score * 100:.1f}%, {top_2.score * 100:.1f}%)"
            ),
        )

    if score_gap >= score_gap_threshold:
        return (
            True,
            section_1,
            (
                f"CONSISTENT: Slide {section_1} leads by {score_gap * 100:.1f}% "
                f"over Slide {section_2}"
            ),
        )
    else:
        return (
            False,
            None,
            (
                f"INCONSISTENT: Slide {section_1} ({top_1.score * 100:.1f}%) vs "
                f"Slide {section_2} ({top_2.score * 100:.1f}%) competing!"
            ),
        )


def print_results(results: list[SimilarityResult], top_n: int = 5) -> None:
    print(f"\n{'-' * 80}")
    print(f"{'#':<3} {'Slide':<7} {'Score':<8} {'Sources':<15} {'Content (40 chars)'}")
    print(f"{'-' * 80}")

    for i, r in enumerate(results[:top_n], 1):
        sections = [s.section_index for s in r.chunk.source_sections]
        sections_str = ",".join(map(str, sections))
        target = r.chunk.source_sections[-1].section_index
        print(
            f"{i:<3} {target:<7} {r.score * 100:.1f}%    {sections_str:<15} {r.chunk.partial_content[:40]}..."
        )

    print(f"{'-' * 80}")


def main() -> None:
    print("=" * 80)
    print("REALISTIC INTERVENTION TEST")
    print("=" * 80)

    sections = create_realistic_sections()
    window_size = 12
    chunks = chunk_producer.generate_chunks(sections, window_size)

    print(
        f"\n[INFO] {len(sections)} slides, {len(chunks)} chunks, window={window_size}"
    )

    calculator = SimilarityCalculator(chunks)
    candidate_gen = chunk_producer.CandidateChunkGenerator(chunks)

    # =========================================================================
    # ANALYSIS: What chunks are candidates when we're on slide 11?
    # =========================================================================
    print("\n" + "=" * 80)
    print("ANALYSIS: Candidate chunks when current_section = 11")
    print("=" * 80)

    current = sections[10]  # Slide 11
    candidates = candidate_gen.get_candidate_chunks(current)

    # Count chunks by their TARGET section (last source section)
    from collections import Counter

    target_counts = Counter(c.source_sections[-1].section_index for c in candidates)

    print(f"\n[CANDIDATES] Total: {len(candidates)} chunks")
    print(f"[BY TARGET SLIDE]:")
    for slide, count in sorted(target_counts.items()):
        print(f"  Slide {slide}: {count} chunks")

    # Check if slide 14 chunks are in candidates
    slide_14_chunks = [
        c for c in candidates if c.source_sections[-1].section_index == 14
    ]
    print(f"\n[CRITICAL] Slide 14 chunks in candidates: {len(slide_14_chunks)}")
    if slide_14_chunks:
        print("  These chunks could cause the system to want to go to slide 14!")
        for c in slide_14_chunks[:3]:
            sources = [s.section_index for s in c.source_sections]
            print(f"    Sources: {sources} | Content: {c.partial_content[:50]}...")

    # =========================================================================
    # SCENARIO 1: Normal - Speaker on slide 14, reading slide 14
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 1: NORMAL")
    print("  Speaker on Slide 14, buffer = 12 words from slide 14")
    print("=" * 80)

    current = sections[13]  # Slide 14
    # Exact words from slide 14
    input_14 = (
        "sonuc olarak urun mukemmel kalitede uretildi musteri memnuniyeti oncelik"
    )

    print(f'\n[INPUT] "{input_14}"')
    print(f"[POSITION] Slide {current.section_index}")

    candidates = candidate_gen.get_candidate_chunks(current)
    print(f"[CANDIDATES] {len(candidates)}")

    results = calculator.compare(input_14, candidates)
    print_results(results)

    is_ok, target, msg = analyze_consistency(results)
    print(f"\n[ANALYSIS] {msg}")
    print(f"[DECISION] {'NAVIGATE -> ' + str(target) if is_ok else 'WAIT'}")

    # =========================================================================
    # SCENARIO 2: Intervention - Supervisor moved to 11, buffer still has slide 14 words
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 2: AFTER MANUAL INTERVENTION")
    print("  Supervisor moved to Slide 11")
    print("  Buffer: 8 words from slide 14 + 4 words from slide 11")
    print("=" * 80)

    current = sections[10]  # Slide 11 (supervisor moved here)

    # Mixed buffer: 8 words from slide 14, 4 words from slide 11
    # Slide 14: "sonuc olarak urun mukemmel kalitede uretildi musteri memnuniyeti"
    # Slide 11: "onceki yil sonuclari buyume"
    input_mixed = "olarak urun mukemmel kalitede uretildi musteri memnuniyeti onceki yil sonuclari buyume"

    print(f'\n[INPUT] "{input_mixed}"')
    print(f"[POSITION] Slide {current.section_index} (set by supervisor)")

    candidates = candidate_gen.get_candidate_chunks(current)
    print(f"[CANDIDATES] {len(candidates)}")

    # Show which target slides are in candidates
    target_slides = set(c.source_sections[-1].section_index for c in candidates)
    print(f"[TARGET SLIDES in candidates] {sorted(target_slides)}")

    results = calculator.compare(input_mixed, candidates)
    print_results(results, top_n=8)

    is_ok, target, msg = analyze_consistency(results)
    print(f"\n[ANALYSIS] {msg}")
    print(f"[DECISION] {'NAVIGATE -> ' + str(target) if is_ok else 'WAIT'}")

    # Check if any results point to slide 14
    slide_14_results = [
        r for r in results if r.chunk.source_sections[-1].section_index == 14
    ]
    if slide_14_results:
        print(f"\n[WARNING] {len(slide_14_results)} results point to slide 14!")
        print(f"  Top slide 14 score: {slide_14_results[0].score * 100:.1f}%")
        if results[0].chunk.source_sections[-1].section_index == 14:
            print("  *** TOP RESULT POINTS TO SLIDE 14 - PROBLEM! ***")

    # =========================================================================
    # SCENARIO 3: Buffer refreshed - all words from slide 11
    # =========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 3: BUFFER REFRESHED")
    print("  Speaker continued on Slide 11, buffer fully refreshed")
    print("=" * 80)

    current = sections[10]  # Slide 11
    # All words from slide 11
    input_11 = "gecmis donem performansi onceki yil sonuclari buyume oranlari kar marji"

    print(f'\n[INPUT] "{input_11}"')
    print(f"[POSITION] Slide {current.section_index}")

    candidates = candidate_gen.get_candidate_chunks(current)
    results = calculator.compare(input_11, candidates)
    print_results(results)

    is_ok, target, msg = analyze_consistency(results)
    print(f"\n[ANALYSIS] {msg}")
    print(f"[DECISION] {'NAVIGATE -> ' + str(target) if is_ok else 'WAIT'}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print("""
    CandidateChunkGenerator filtering:
    - When on slide 11, only chunks with min_section+3 >= 11 or max_section-2 <= 11 are candidates
    - This means pure slide 14 chunks (source=[14]) are NOT candidates when on slide 11
    - BUT transition chunks (source=[13,14] or similar) MAY be candidates
    
    The protection is PARTIAL:
    - Pure distant chunks are filtered out (good!)
    - Transition chunks near the boundary may still cause issues
    """)


if __name__ == "__main__":
    import io
    import sys
    from pathlib import Path

    # Capture output
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf

    main()

    sys.stdout = old
    text = buf.getvalue()

    # Save and print
    out = Path(__file__).parent / "test_realistic_output.txt"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n[Saved to: {out}]")
