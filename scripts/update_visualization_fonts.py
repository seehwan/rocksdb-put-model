#!/usr/bin/env python3
"""
Update all visualizations to use Times font family, 18pt or larger

모든 시각화 생성 스크립트의 폰트 설정 업데이트
"""

import os
import re

# Font configuration for all visualizations
FONT_CONFIG = """
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Times font 설정
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 18
plt.rcParams['axes.titlesize'] = 20
plt.rcParams['axes.labelsize'] = 18
plt.rcParams['xtick.labelsize'] = 18
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['legend.fontsize'] = 16
plt.rcParams['figure.titlesize'] = 22
plt.rcParams['axes.unicode_minus'] = False

# Fallback fonts
plt.rcParams['font.sans-serif'] = ['Times New Roman', 'Liberation Serif', 'DejaVu Serif']
"""

# Find all visualization scripts
viz_scripts = [
    'scripts/generate_rate_control_visualization.py',
    'scripts/generate_model_parameter_visualization.py',
    'scripts/generate_wa_ra_sensitivity_visualization.py'
]

def update_script_fonts(script_path):
    """Update font settings in a script"""
    
    if not os.path.exists(script_path):
        print(f"⚠️  Script not found: {script_path}")
        return False
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Check if already has correct font settings
    if "plt.rcParams['font.family'] = 'Times New Roman'" in content:
        print(f"✅ {script_path} already updated")
        return True
    
    # Find plt.rcParams sections
    # Replace or add font configuration
    
    # Method 1: Replace existing font settings
    content = re.sub(
        r"plt\.rcParams\['font\.family'\]\s*=\s*['\"].*?['\"]",
        "plt.rcParams['font.family'] = 'Times New Roman'",
        content
    )
    
    content = re.sub(
        r"plt\.rcParams\['font\.size'\]\s*=\s*\d+",
        "plt.rcParams['font.size'] = 18",
        content
    )
    
    content = re.sub(
        r"plt\.rcParams\['axes\.labelsize'\]\s*=\s*\d+",
        "plt.rcParams['axes.labelsize'] = 18",
        content
    )
    
    content = re.sub(
        r"plt\.rcParams\['xtick\.labelsize'\]\s*=\s*\d+",
        "plt.rcParams['xtick.labelsize'] = 18",
        content
    )
    
    content = re.sub(
        r"plt\.rcParams\['ytick\.labelsize'\]\s*=\s*\d+",
        "plt.rcParams['ytick.labelsize'] = 18",
        content
    )
    
    content = re.sub(
        r"plt\.rcParams\['legend\.fontsize'\]\s*=\s*\d+",
        "plt.rcParams['legend.fontsize'] = 16",
        content
    )
    
    # Add Times font imports if not present
    if "import matplotlib.pyplot as plt" in content and "Times" not in content[:500]:
        # Insert after imports
        content = content.replace(
            "import matplotlib.pyplot as plt",
            "import matplotlib.pyplot as plt\nfrom matplotlib import font_manager"
        )
        
        # Add font config block after imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'import matplotlib' in line:
                # Find the end of imports
                for j in range(i+1, min(i+20, len(lines))):
                    if lines[j].strip() == '' or lines[j].startswith('def ') or lines[j].startswith('class '):
                        insert_idx = j
                        break
                else:
                    insert_idx = i + 2
                
                font_config = '''
# Times font 설정 (18pt or larger)
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 18
plt.rcParams['axes.titlesize'] = 20
plt.rcParams['axes.labelsize'] = 18
plt.rcParams['xtick.labelsize'] = 18
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['legend.fontsize'] = 16
plt.rcParams['figure.titlesize'] = 22
plt.rcParams['axes.unicode_minus'] = False
'''
                
                lines.insert(insert_idx, font_config)
                content = '\n'.join(lines)
                break
    
    # Write updated content
    with open(script_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated: {script_path}")
    return True

def main():
    """Update all visualization scripts"""
    print("=" * 80)
    print("Updating visualization fonts to Times, 18pt or larger")
    print("=" * 80)
    
    for script in viz_scripts:
        update_script_fonts(script)
    
    print("\n" + "=" * 80)
    print("✅ All visualization scripts updated!")
    print("=" * 80)
    print("\nNext step: Regenerate all visualizations with new fonts")
    print("Run: python scripts/generate_rate_control_visualization.py")
    print("     python scripts/generate_model_parameter_visualization.py")
    print("     python scripts/generate_wa_ra_sensitivity_visualization.py")


if __name__ == "__main__":
    main()

