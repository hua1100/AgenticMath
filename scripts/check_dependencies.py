#!/usr/bin/env python3
"""
Dependency Validation Script for AgenticMath

Checks that all required dependencies are installed and functioning correctly.
Run this before deployment to catch dependency issues early.
"""

import sys
import importlib
from typing import List, Tuple, Dict
import platform


class DependencyChecker:
    """Validates system and Python dependencies."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []

    def check_python_version(self) -> bool:
        """Check Python version is 3.11+."""
        print("Checking Python version...")
        version = sys.version_info

        if version.major == 3 and version.minor >= 11:
            self.success.append(f"✓ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.errors.append(
                f"✗ Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}"
            )
            return False

    def check_python_package(self, package_name: str, import_name: str = None) -> bool:
        """Check if a Python package can be imported."""
        import_name = import_name or package_name

        try:
            module = importlib.import_module(import_name)
            version = getattr(module, "__version__", "unknown")
            self.success.append(f"✓ {package_name} ({version})")
            return True
        except ImportError as e:
            self.errors.append(f"✗ {package_name}: {str(e)}")
            return False
        except Exception as e:
            self.warnings.append(f"⚠ {package_name} imported but error: {str(e)}")
            return True

    def check_opencv(self) -> bool:
        """Check OpenCV with special validation."""
        print("Checking OpenCV...")

        try:
            import cv2
            version = cv2.__version__
            self.success.append(f"✓ opencv-python ({version})")

            # Test basic functionality
            import numpy as np
            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
            gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)

            self.success.append("✓ OpenCV basic operations working")
            return True

        except ImportError:
            self.errors.append("✗ opencv-python not installed")
            return False
        except Exception as e:
            self.errors.append(f"✗ OpenCV error: {str(e)}")
            self.errors.append("  Hint: Missing system libraries (libGL, libgthread, etc.)")
            return False

    def check_paddleocr(self) -> bool:
        """Check PaddleOCR with special validation."""
        print("Checking PaddleOCR...")

        try:
            from paddleocr import PaddleOCR
            self.success.append("✓ PaddleOCR imported successfully")

            # Test initialization (without actually running inference)
            try:
                ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    show_log=False,
                    use_gpu=False
                )
                self.success.append("✓ PaddleOCR initialization successful")
                return True
            except Exception as init_error:
                self.warnings.append(f"⚠ PaddleOCR imported but initialization failed: {init_error}")
                self.warnings.append("  This may be OK if models will be downloaded on first use")
                return True

        except ImportError as e:
            self.errors.append(f"✗ PaddleOCR import failed: {str(e)}")
            return False
        except Exception as e:
            self.errors.append(f"✗ PaddleOCR error: {str(e)}")
            return False

    def check_database_driver(self) -> bool:
        """Check PostgreSQL driver."""
        print("Checking database drivers...")

        try:
            import psycopg2
            self.success.append(f"✓ psycopg2 ({psycopg2.__version__})")
            return True
        except ImportError:
            self.errors.append("✗ psycopg2-binary not installed")
            return False
        except Exception as e:
            self.warnings.append(f"⚠ psycopg2 issue: {str(e)}")
            return True

    def check_core_packages(self) -> bool:
        """Check all core Python packages."""
        print("Checking core packages...")

        packages = [
            ("openai", "openai"),
            ("pydantic", "pydantic"),
            ("sqlalchemy", "sqlalchemy"),
            ("fastapi", "fastapi"),
            ("click", "click"),
            ("rich", "rich"),
            ("pytest", "pytest"),
            ("Pillow", "PIL"),
            ("numpy", "numpy"),
        ]

        all_ok = True
        for package_name, import_name in packages:
            if not self.check_python_package(package_name, import_name):
                all_ok = False

        return all_ok

    def check_system_info(self):
        """Display system information."""
        print("\nSystem Information:")
        print(f"  Platform: {platform.system()} {platform.release()}")
        print(f"  Architecture: {platform.machine()}")
        print(f"  Python: {platform.python_version()}")
        print("")

    def run_all_checks(self) -> bool:
        """Run all dependency checks."""
        print("=" * 60)
        print("AgenticMath Dependency Checker")
        print("=" * 60)
        print("")

        self.check_system_info()

        checks = [
            self.check_python_version(),
            self.check_core_packages(),
            self.check_opencv(),
            self.check_paddleocr(),
            self.check_database_driver(),
        ]

        print("\n" + "=" * 60)
        print("Results:")
        print("=" * 60)

        if self.success:
            print(f"\n✓ Successfully validated ({len(self.success)}):")
            for msg in self.success:
                print(f"  {msg}")

        if self.warnings:
            print(f"\n⚠ Warnings ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"  {msg}")

        if self.errors:
            print(f"\n✗ Errors ({len(self.errors)}):")
            for msg in self.errors:
                print(f"  {msg}")
            print("\nDependency check FAILED!")
            return False

        print("\n" + "=" * 60)
        if self.warnings:
            print("✓ Dependency check PASSED with warnings")
            print("  Review warnings above before deploying to production")
        else:
            print("✓ All dependency checks PASSED!")
        print("=" * 60)

        return True


def main():
    """Main entry point."""
    checker = DependencyChecker()
    success = checker.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
