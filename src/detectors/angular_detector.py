import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from src.io.frames import FrameData

MAX_RANGE_M = 3.5  # Maximum range for the bounding box in meters

@dataclass
class AngularBounds:
    """Defines an angular sector in camera space."""
    azimuth_center: float  # Degrees, 0 = center, negative = left, positive = right
    azimuth_span: float    # Degrees, total width of sector
    elevation_center: float = -10.0  # Degrees, 0 = center, negative = down, positive = up    
    elevation_span: float = 10.0  # Degrees, total height centered on 0
    min_range: float = 0.5  # Minimum detection distance in meters
    max_range: float = MAX_RANGE_M  # Maximum detection distance in meters

@dataclass
class SectorDetection:
    """Detection result for an angular sector."""
    min_distance_m: float
    num_valid_points: int
    azimuth_deg: float
    valid_mask: np.ndarray  # Mask of valid points in the sector

@dataclass
class Sector:
    """Represents a virtual piano sector in angular space."""
    name: str
    color: tuple[int, int, int]
    bounds: AngularBounds
    _cached_mask: np.ndarray | None = field(default=None, init=False, repr=False)
    _cached_intrinsics_key: tuple[int, int, float, float, float, float] | None = field(default=None, init=False, repr=False)
    _min_depth_mm: int = field(default=0, init=False, repr=False)
    _max_depth_mm: int = field(default=0, init=False, repr=False)

    def ensure_cache(self, intrinsics) -> None:
        intrinsics_key = (
            intrinsics.width,
            intrinsics.height,
            intrinsics.fx,
            intrinsics.fy,
            intrinsics.ppx,
            intrinsics.ppy,
        )
        if self._cached_intrinsics_key != intrinsics_key:
            self._cached_mask = _build_angular_mask(intrinsics, self.bounds)
            self._cached_intrinsics_key = intrinsics_key
            self._min_depth_mm = int(self.bounds.min_range * 1000)
            self._max_depth_mm = int(self.bounds.max_range * 1000)

    def detect(self, frame_data: FrameData) -> Optional[SectorDetection]:
        self.ensure_cache(frame_data.depth_intrinsics)

        valid_mask = self._cached_mask & (frame_data.depth_image > self._min_depth_mm) & (frame_data.depth_image < self._max_depth_mm)
        if not np.any(valid_mask):
            return None

        depth_points = frame_data.depth_image[valid_mask]
        return SectorDetection(
            min_distance_m=float(np.min(depth_points)) / 1000.0,
            num_valid_points=int(np.count_nonzero(valid_mask)),
            azimuth_deg=self.bounds.azimuth_center,
            valid_mask=valid_mask,
        )


def _build_angular_mask(intrinsics, bounds: AngularBounds) -> np.ndarray:
    """Create a cached boolean mask for pixels that fall inside the sector angles."""
    height = intrinsics.height
    width = intrinsics.width
    px = np.arange(width, dtype=np.float32)
    py = np.arange(height, dtype=np.float32)
    azimuth = np.rad2deg(np.arctan2(px - intrinsics.ppx, intrinsics.fx))
    elevation = np.rad2deg(np.arctan2(py - intrinsics.ppy, intrinsics.fy))

    half_az_span = bounds.azimuth_span / 2
    half_el_span = bounds.elevation_span / 2

    azimuth_mask = (azimuth >= bounds.azimuth_center - half_az_span) & (azimuth <= bounds.azimuth_center + half_az_span)
    elevation_mask = (elevation >= bounds.elevation_center - half_el_span) & (elevation <= bounds.elevation_center + half_el_span)
    return elevation_mask[:, np.newaxis] & azimuth_mask[np.newaxis, :]