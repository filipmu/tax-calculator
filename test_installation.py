#!/usr/bin/env python3
"""
Quick installation test for the taxcalc package.

Run this script to verify the package is installed correctly:
    python test_installation.py
"""

def test_installation():
    """Test that the package is installed and working."""

    print("Testing taxcalc package installation...\n")

    try:
        # Test 1: Import package
        print("✓ Test 1: Importing package...", end=" ")
        from taxcalc import (
            FilingStatus,
            Person,
            TaxUnit,
            Income,
            ItemizedDeductions,
            TaxCalculator2024
        )
        print("PASSED")

        # Test 2: Create basic objects
        print("✓ Test 2: Creating data objects...", end=" ")
        taxpayer = TaxUnit(
            filing_status=FilingStatus.SINGLE,
            primary=Person(age=30),
            income=Income(wages_w2=100000)
        )
        itemized = ItemizedDeductions()
        print("PASSED")

        # Test 3: Run calculation
        print("✓ Test 3: Running tax calculation...", end=" ")
        calc = TaxCalculator2024(taxpayer, itemized)
        results = calc.calculate_all_taxes()
        print("PASSED")

        # Test 4: Verify results
        print("✓ Test 4: Verifying results...", end=" ")
        assert results.gross_income == 100000, "Gross income mismatch"
        assert results.total_tax_liability > 0, "Tax liability should be positive"
        assert results.effective_total_rate > 0, "Effective rate should be positive"
        print("PASSED")

        # Test 5: Generate report
        print("✓ Test 5: Generating report...", end=" ")
        report = calc.generate_summary_report(results)
        assert len(report) > 0, "Report should not be empty"
        assert "TAX CALCULATION SUMMARY" in report, "Report should contain header"
        print("PASSED")

        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nPackage is correctly installed and working.")
        print("\nQuick calculation results:")
        print(f"  Income:         ${results.gross_income:>12,.2f}")
        print(f"  Federal Tax:    ${results.total_federal_tax:>12,.2f}")
        print(f"  California Tax: ${results.total_california_tax:>12,.2f}")
        print(f"  Total Tax:      ${results.total_tax_liability:>12,.2f}")
        print(f"  Effective Rate: {results.effective_total_rate*100:>12.2f}%")
        print("\nNext steps:")
        print("  1. Open examples/tax_analysis_example.ipynb in Jupyter Lab")
        print("  2. Run: python examples/simple_example.py")
        print("  3. Check QUICKSTART.md for usage guide")

        return True

    except ImportError as e:
        print(f"FAILED\n\nError: {e}")
        print("\nPackage not found. Try installing it:")
        print("  cd /home/azhar/tax-calculator")
        print("  source venv/bin/activate")
        print("  pip install -e .")
        return False

    except Exception as e:
        print(f"FAILED\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_installation()
    sys.exit(0 if success else 1)
