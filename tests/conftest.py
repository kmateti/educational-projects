import pytest
import cv2

def pytest_addoption(parser):
    parser.addoption(
        "--showgui",
        action="store_true",
        default=False,
        help="show GUI windows during tests"
    )

@pytest.fixture
def show_gui(request):
    """Fixture to control GUI window display in tests."""
    return request.config.getoption("--showgui")