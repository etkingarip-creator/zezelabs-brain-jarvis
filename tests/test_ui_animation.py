import math
import pytest

def calculate_distance_warp(node_x, node_y, mouse_x, mouse_y, threshold=85):
    """
    Simulated distance warping coordinates scaling.
    Identical to the implementation in JarvisDesktopApp.animate_neural_network.
    """
    dx = mouse_x - node_x
    dy = mouse_y - node_y
    dist = math.hypot(dx, dy)
    
    if dist < threshold:
        warp_factor = (threshold - dist) / threshold
        target_x = node_x + dx * warp_factor * 0.25
        target_y = node_y + dy * warp_factor * 0.25
        return target_x, target_y, True
    return node_x, node_y, False

def test_distance_proximity_warping():
    node_x, node_y = 100, 100
    
    # Test case 1: Mouse far away (no warp)
    tx, ty, warped = calculate_distance_warp(node_x, node_y, 300, 300)
    assert not warped
    assert tx == node_x
    assert ty == node_y
    
    # Test case 2: Mouse extremely close (heavy warp closer to mouse)
    tx, ty, warped = calculate_distance_warp(node_x, node_y, 110, 110)
    assert warped
    assert tx > node_x  # Pulled towards 110
    assert ty > node_y
    # Warp distance should be modest (elastic interpolation)
    assert tx < 110
    assert ty < 110

def test_pulsing_amplitude_oscillation():
    # Breathing oscillation math validation
    phases = [0.0, math.pi / 2, math.pi, math.pi * 1.5, math.pi * 2]
    radii = []
    
    base_r = 6
    for phase in phases:
        offset = math.sin(phase) * 1.5
        r = base_r + offset
        radii.append(r)
        
    assert radii[0] == 6.0
    assert radii[1] == 7.5
    assert radii[2] == 6.0
    assert radii[3] == 4.5
    assert radii[4] == 6.0
