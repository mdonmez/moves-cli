"""
Test script to demonstrate Top-N consistency analysis for manual intervention handling.

This test simulates:
1. Normal scenario: Speaker is on slide 14, buffer is consistent
2. Intervention scenario: Supervisor moves to slide 11, buffer contains mixed words
3. Recovery scenario: Buffer fully refreshed with slide 11 content

Run with: uv run python tests/test_top_n_consistency.py
"""

from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.models import Section, SimilarityResult


def create_test_sections() -> list[Section]:
    """Create test sections simulating a presentation."""
    return [
        Section(
            content="baslangic acilis konusmasi hos geldiniz etkinligimize bugun sizlerle birlikteyiz",
            section_index=1,
        ),
        Section(
            content="gundem maddelerimiz sirket tanitimi urun lansmani soru cevap bolumu kapanis",
            section_index=2,
        ),
        Section(
            content="sirketimiz iki bin yirmi yilinda kuruldu teknoloji sektorunde faaliyet gosteriyoruz",
            section_index=3,
        ),
        Section(
            content="ekibimiz yirmi bes kisiden olusuyor yazilim muhendisleri tasarimcilar proje yoneticileri",
            section_index=4,
        ),
        Section(
            content="vizyonumuz dijital donusumde lider olmak musterilerimize en iyi hizmeti sunmak",
            section_index=5,
        ),
        Section(
            content="misyonumuz yenilikci cozumler uretmek surdurulebilir buyume saglamak kalite standartlarini yukseltmek",
            section_index=6,
        ),
        Section(
            content="degerlerimiz musteri odaklilik seffaflik surekli gelisim takim calismasi inovasyon",
            section_index=7,
        ),
        Section(
            content="urunlerimiz bulut tabanli cozumler mobil uygulamalar yapay zeka servisleri veri analitigi",
            section_index=8,
        ),
        Section(
            content="yeni urunumuz akilli asistan platformu dogal dil isleme yapay zeka destekli",
            section_index=9,
        ),
        Section(
            content="platform ozellikleri sesli komut destegi coklu dil anlama baglam farkindaligi",
            section_index=10,
        ),
        Section(
            content="gecen yil basladik projeye ve arastirma asamasinda cok onemli bulgular elde ettik",
            section_index=11,
        ),
        Section(
            content="arastirma sonuclari kullanici testleri performans olcumleri guvenlik denetimleri basarili oldu",
            section_index=12,
        ),
        Section(
            content="lansmaniniz onumuzdeki ay gerceklesecek global pazarda es zamanli sunuluyor olacak",
            section_index=13,
        ),
        Section(
            content="urun kaliteli malzeme ile uretildi ve musteri memnuniyeti icin ozel olarak tasarlandi",
            section_index=14,
        ),
        Section(
            content="fiyatlandirma modeli aylik abonelik yillik paket kurumsal lisans secenekleri mevcut",
            section_index=15,
        ),
    ]


def analyze_top_n_consistency(
    results: list[SimilarityResult],
    score_gap_threshold: float = 0.05,  # Lowered to 5%
) -> tuple[bool, int | None, str]:
    """
    Analyze top 2 results for consistency.

    Logic:
    1. If Top 1 and Top 2 point to SAME slide -> Consistent (strong consensus)
    2. If Top 1 and Top 2 point to DIFFERENT slides:
       - If score gap >= threshold -> Top 1 is dominant, consistent
       - If score gap < threshold -> Competing slides, inconsistent (wait)

    Returns:
        tuple: (is_confident, target_section_index, analysis_message)
    """
    if len(results) < 2:
        section = results[0].chunk.source_sections[-1].section_index
        return True, section, f"CONSISTENT: Single result points to Slide {section}"

    top_1 = results[0]
    top_2 = results[1]

    section_1 = top_1.chunk.source_sections[-1].section_index
    section_2 = top_2.chunk.source_sections[-1].section_index

    score_gap = top_1.score - top_2.score

    # Case 1: Top 1 and Top 2 point to SAME slide - strong consensus!
    if section_1 == section_2:
        return (
            True,
            section_1,
            (
                f"CONSISTENT: Top 2 results both point to Slide {section_1} "
                f"({top_1.score * 100:.1f}% and {top_2.score * 100:.1f}%)"
            ),
        )

    # Case 2: Different slides - check if Top 1 has clear lead
    if score_gap >= score_gap_threshold:
        return (
            True,
            section_1,
            (
                f"CONSISTENT: Slide {section_1} leads by {score_gap * 100:.1f}% "
                f"over Slide {section_2} (threshold: {score_gap_threshold * 100:.1f}%)"
            ),
        )
    else:
        return (
            False,
            None,
            (
                f"INCONSISTENT: Slide {section_1} ({top_1.score * 100:.1f}%) vs "
                f"Slide {section_2} ({top_2.score * 100:.1f}%) - "
                f"gap only {score_gap * 100:.1f}%, slides are competing!"
            ),
        )


def print_top_results(results: list[SimilarityResult], top_n: int = 5) -> None:
    """Print top N results in a formatted way."""
    print(f"\n{'-' * 70}")
    print(f"{'Rank':<6} {'Slide':<8} {'Score':<10} {'Chunk Content (first 40 chars)'}")
    print(f"{'-' * 70}")

    for i, result in enumerate(results[:top_n], 1):
        section_idx = result.chunk.source_sections[-1].section_index
        score_pct = f"{result.score * 100:.1f}%"
        content_preview = result.chunk.partial_content[:40] + "..."
        print(f"{i:<6} {section_idx:<8} {score_pct:<10} {content_preview}")

    print(f"{'-' * 70}")


def main() -> None:
    print("=" * 70)
    print("TOP-N CONSISTENCY ANALYSIS TEST")
    print("=" * 70)

    # Create sections and chunks
    sections = create_test_sections()
    window_size = 12
    chunks = chunk_producer.generate_chunks(sections, window_size)

    print(f"\n[INFO] {len(sections)} slides and {len(chunks)} chunks created")
    print(f"[INFO] Window size: {window_size} words")

    # Initialize similarity calculator
    calculator = SimilarityCalculator(chunks)

    # Get candidate chunks generator
    candidate_generator = chunk_producer.CandidateChunkGenerator(chunks)

    # =========================================================================
    # SCENARIO 1: NORMAL SITUATION
    # =========================================================================
    print("\n" + "=" * 70)
    print("SCENARIO 1: NORMAL SITUATION")
    print("  Speaker is on Slide 14, buffer is fully consistent")
    print("=" * 70)

    # Simulate current section
    current_section = sections[13]  # Section index 14 (0-indexed: 13)

    # Input: Last 12 words from slide 14
    input_normal = (
        "urun kaliteli malzeme ile uretildi ve musteri memnuniyeti icin ozel tasarlandi"
    )
    print(f'\n[INPUT] "{input_normal}"')
    print(f"[POSITION] Current slide: {current_section.section_index}")

    # Get candidate chunks
    candidates = candidate_generator.get_candidate_chunks(current_section)
    print(f"[CANDIDATES] {len(candidates)} candidate chunks")

    # Compare
    results = calculator.compare(input_normal, candidates)
    print_top_results(results)

    # Analyze consistency
    is_confident, target, message = analyze_top_n_consistency(results)
    print(f"\n[ANALYSIS] {message}")
    print(
        f"[DECISION] {'NAVIGATE -> Slide ' + str(target) if is_confident else 'WAIT'}"
    )

    # =========================================================================
    # SCENARIO 2: AFTER MANUAL INTERVENTION (DIRTY BUFFER)
    # =========================================================================
    print("\n" + "=" * 70)
    print("SCENARIO 2: AFTER MANUAL INTERVENTION")
    print(
        "  Supervisor moved to Slide 11, buffer is mixed (8 words from Slide 14, 4 from Slide 11)"
    )
    print("=" * 70)

    # After intervention, current section is now 11
    current_section = sections[10]  # Section index 11 (0-indexed: 10)

    # Input: Mixed words (8 from slide 14 + 4 from slide 11)
    input_mixed = (
        "malzeme ile uretildi ve musteri memnuniyeti gecen yil basladik projeye"
    )
    print(f'\n[INPUT] "{input_mixed}"')
    print(
        f"[POSITION] Current slide (set by supervisor): {current_section.section_index}"
    )

    # Get candidate chunks for new position
    candidates = candidate_generator.get_candidate_chunks(current_section)
    print(f"[CANDIDATES] {len(candidates)} candidate chunks")

    # Compare
    results = calculator.compare(input_mixed, candidates)
    print_top_results(results)

    # Analyze consistency
    is_confident, target, message = analyze_top_n_consistency(results)
    print(f"\n[ANALYSIS] {message}")
    print(
        f"[DECISION] {'NAVIGATE -> Slide ' + str(target) if is_confident else 'WAIT (do not override supervisor)'}"
    )

    # =========================================================================
    # SCENARIO 3: BUFFER FULLY REFRESHED
    # =========================================================================
    print("\n" + "=" * 70)
    print("SCENARIO 3: BUFFER FULLY REFRESHED")
    print("  Speaker continued reading Slide 11, buffer is now fully refreshed")
    print("=" * 70)

    # Current section is still 11
    current_section = sections[10]  # Section index 11 (0-indexed: 10)

    # Input: All words from slide 11
    input_refreshed = (
        "gecen yil basladik projeye ve arastirma asamasinda cok onemli bulgular elde"
    )
    print(f'\n[INPUT] "{input_refreshed}"')
    print(f"[POSITION] Current slide: {current_section.section_index}")

    # Get candidate chunks
    candidates = candidate_generator.get_candidate_chunks(current_section)
    print(f"[CANDIDATES] {len(candidates)} candidate chunks")

    # Compare
    results = calculator.compare(input_refreshed, candidates)
    print_top_results(results)

    # Analyze consistency
    is_confident, target, message = analyze_top_n_consistency(results)
    print(f"\n[ANALYSIS] {message}")
    print(
        f"[DECISION] {'NAVIGATE -> Slide ' + str(target) if is_confident else 'WAIT'}"
    )

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
    SCENARIO 1 (Normal):     Buffer consistent    -> Navigation allowed
    SCENARIO 2 (Intervened): Buffer mixed         -> Wait, don't override
    SCENARIO 3 (Refreshed):  Buffer refreshed     -> Navigation allowed
    
    This approach:
    - Uses existing API (compare() already returns sorted list)
    - Doesn't change chunk size (still 12 words)
    - Only adds consistency check to decision mechanism
    - Doesn't need to "know" about intervention, detects inconsistency
    """)


if __name__ == "__main__":
    import io
    from pathlib import Path

    # Capture output
    output_buffer = io.StringIO()
    import sys

    old_stdout = sys.stdout
    sys.stdout = output_buffer

    main()

    sys.stdout = old_stdout
    output_text = output_buffer.getvalue()

    # Write to file
    output_path = Path(__file__).parent / "test_output.txt"
    output_path.write_text(output_text, encoding="utf-8")

    # Also print to console
    print(output_text)
    print(f"\n[Output also saved to: {output_path}]")
