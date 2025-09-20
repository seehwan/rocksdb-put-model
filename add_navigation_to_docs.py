#!/usr/bin/env python3
"""
Add navigation to all HTML documents
"""

import re

def add_navigation_to_html(filename, current_title, category):
    """Add navigation to HTML document"""
    
    # Navigation CSS
    nav_css = """
        /* Document Navigation Styles */
        .document-navigation {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 25px;
            margin: 30px 0;
        }
        
        .nav-header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .nav-header h4 {
            margin: 0 0 5px 0;
            color: #2c3e50;
            font-size: 1.3em;
        }
        
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .nav-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .nav-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .nav-card.current-doc {
            border: 2px solid #007bff;
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        }
        
        .nav-icon {
            font-size: 1.5em;
            margin-bottom: 8px;
        }
        
        .nav-card h5 {
            margin: 0 0 8px 0;
            color: #2c3e50;
            font-size: 1em;
        }
        
        .nav-card p {
            margin: 0 0 10px 0;
            color: #6c757d;
            font-size: 0.85em;
        }
        
        .nav-links {
            display: flex;
            gap: 8px;
            justify-content: center;
        }
        
        .nav-links a {
            background: #007bff;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.8em;
            transition: background 0.3s ease;
        }
        
        .nav-links a:hover {
            background: #0056b3;
        }
        
        .quick-links {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
        }
        
        .quick-links h4 {
            margin: 0 0 15px 0;
            color: #856404;
        }
        
        .links-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .link-group {
            background: white;
            padding: 12px;
            border-radius: 5px;
            border: 1px solid #ffeaa7;
        }
        
        .link-group h5 {
            margin: 0 0 8px 0;
            color: #495057;
            font-size: 0.9em;
        }
        
        .link-group a {
            display: block;
            color: #007bff;
            text-decoration: none;
            margin: 3px 0;
            font-size: 0.85em;
        }
        
        .footer-navigation {
            background: #2c3e50;
            color: white;
            padding: 30px;
            margin-top: 50px;
            border-radius: 10px;
        }
        
        .footer-nav-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 25px;
        }
        
        .footer-section h5 {
            margin: 0 0 12px 0;
            color: #ecf0f1;
            font-size: 1em;
        }
        
        .footer-section ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .footer-section a {
            color: #bdc3c7;
            text-decoration: none;
            font-size: 0.9em;
            transition: color 0.3s ease;
        }
        
        .footer-section a:hover {
            color: #3498db;
            text-decoration: underline;
        }"""
    
    # Navigation components
    nav_components = {
        'specifications': {
            'current_card': 'Complete Model Specifications',
            'quick_links': """
                <div class="link-group">
                    <h5>📊 For Context</h5>
                    <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🎯 Main Analysis</a>
                    <a href="PHASE_BASED_DETAILED_ANALYSIS.html">📈 Phase Details</a>
                </div>
                <div class="link-group">
                    <h5>🛠️ For Implementation</h5>
                    <a href="TECHNICAL_IMPLEMENTATION_GUIDE.html">🔧 Production Code</a>
                    <a href="index.html">🏠 Main Page</a>
                </div>"""
        },
        'implementation': {
            'current_card': 'Technical Implementation Guide',
            'quick_links': """
                <div class="link-group">
                    <h5>📊 For Understanding</h5>
                    <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🎯 Model Analysis</a>
                    <a href="COMPLETE_MODEL_SPECIFICATIONS.html">🔬 Model Internals</a>
                </div>
                <div class="link-group">
                    <h5>📈 For Details</h5>
                    <a href="PHASE_BASED_DETAILED_ANALYSIS.html">📈 Phase Analysis</a>
                    <a href="index.html">🏠 Main Page</a>
                </div>"""
        },
        'phase_analysis': {
            'current_card': 'Phase-Based Detailed Analysis',
            'quick_links': """
                <div class="link-group">
                    <h5>📊 For Context</h5>
                    <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🎯 Main Analysis</a>
                    <a href="COMPLETE_MODEL_SPECIFICATIONS.html">🔬 Model Internals</a>
                </div>
                <div class="link-group">
                    <h5>🛠️ For Implementation</h5>
                    <a href="TECHNICAL_IMPLEMENTATION_GUIDE.html">🔧 Production Code</a>
                    <a href="index.html">🏠 Main Page</a>
                </div>"""
        }
    }
    
    # Standard navigation header
    nav_header = """
        <div class="document-navigation">
            <div class="nav-header">
                <h4>📚 Document Navigation</h4>
                <p>Complete RocksDB Put-Rate Model Documentation</p>
            </div>
            <div class="nav-grid">
                <div class="nav-card{}">
                    <div class="nav-icon">🎯</div>
                    <h5>Complete V4/V5 Model Analysis</h5>
                    <p>Comprehensive comparison with dual-structure theory</p>
                    <div class="nav-links">
                        <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.md">📄 Markdown</a>
                        <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🌐 HTML</a>
                    </div>
                </div>
                <div class="nav-card{}">
                    <div class="nav-icon">🔬</div>
                    <h5>Complete Model Specifications</h5>
                    <p>Detailed algorithms, mathematics, and internal mechanisms</p>
                    <div class="nav-links">
                        <a href="COMPLETE_MODEL_SPECIFICATIONS.md">📄 Markdown</a>
                        <a href="COMPLETE_MODEL_SPECIFICATIONS.html">🌐 HTML</a>
                    </div>
                </div>
                <div class="nav-card{}">
                    <div class="nav-icon">🔧</div>
                    <h5>Technical Implementation Guide</h5>
                    <p>Production-ready code and deployment guide</p>
                    <div class="nav-links">
                        <a href="TECHNICAL_IMPLEMENTATION_GUIDE.md">📄 Markdown</a>
                        <a href="TECHNICAL_IMPLEMENTATION_GUIDE.html">🌐 HTML</a>
                    </div>
                </div>
                <div class="nav-card{}">
                    <div class="nav-icon">📈</div>
                    <h5>Phase-Based Detailed Analysis</h5>
                    <p>In-depth analysis of Initial, Middle, and Final phases</p>
                    <div class="nav-links">
                        <a href="PHASE_BASED_DETAILED_ANALYSIS.md">📄 Markdown</a>
                        <a href="PHASE_BASED_DETAILED_ANALYSIS.html">🌐 HTML</a>
                    </div>
                </div>
            </div>
        </div>""".format(
        ' current-doc' if 'Analysis' in current_title else '',
        ' current-doc' if 'Specifications' in current_title else '',
        ' current-doc' if 'Implementation' in current_title else '',
        ' current-doc' if 'Phase-Based' in current_title else ''
    )
    
    # Footer navigation
    footer_nav = """
        <div class="footer-navigation">
            <div class="footer-nav-content">
                <div class="footer-section">
                    <h5>📚 Main Documents</h5>
                    <ul>
                        <li><a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🎯 Complete Analysis</a></li>
                        <li><a href="COMPLETE_MODEL_SPECIFICATIONS.html">🔬 Model Specifications</a></li>
                        <li><a href="TECHNICAL_IMPLEMENTATION_GUIDE.html">🔧 Implementation Guide</a></li>
                        <li><a href="PHASE_BASED_DETAILED_ANALYSIS.html">📈 Phase Analysis</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h5>🎨 Visualizations</h5>
                    <ul>
                        <li><a href="v4_v5_performance_comparison.png">📊 Performance Comparison</a></li>
                        <li><a href="dual_structure_analysis.png">🔄 Dual-Structure Analysis</a></li>
                        <li><a href="phase_analysis.png">📈 Phase Evolution</a></li>
                        <li><a href="experimental_validation.png">🧪 Experimental Validation</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h5>🏠 Project Home</h5>
                    <ul>
                        <li><a href="index.html">🏠 Main Page</a></li>
                        <li><a href="README.md">📄 README</a></li>
                        <li><a href="FINAL_PROJECT_STRUCTURE.md">📁 Project Structure</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h5>📖 Legacy Docs</h5>
                    <ul>
                        <li><a href="models.html">📊 Model History</a></li>
                        <li><a href="experiments.html">🧪 Experiments</a></li>
                        <li><a href="PutModel_v4.html">📄 V4 Original</a></li>
                    </ul>
                </div>
            </div>
        </div>"""
    
    # Quick links
    quick_links = f"""
        <div class="quick-links">
            <h4>🔗 Quick Navigation</h4>
            <div class="links-grid">
                {nav_components[category]['quick_links']}
            </div>
        </div>"""
    
    return nav_css, nav_header, quick_links, footer_nav

def update_html_file(filename, current_title, category):
    """Update HTML file with navigation"""
    
    print(f"📄 Updating {filename}...")
    
    # Read current file
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get navigation components
    nav_css, nav_header, quick_links, footer_nav = add_navigation_to_html(filename, current_title, category)
    
    # Add CSS to existing styles
    if nav_css not in content:
        # Find the end of existing styles
        style_end = content.find('    </style>')
        if style_end != -1:
            content = content[:style_end] + nav_css + '\n' + content[style_end:]
    
    # Add navigation header after the main header
    if 'document-navigation' not in content:
        # Find where to insert navigation (after header div)
        header_end = content.find('        </div>\n\n        <div class="section">')
        if header_end != -1:
            insert_pos = header_end + len('        </div>')
            content = content[:insert_pos] + '\n\n' + nav_header + '\n\n' + quick_links + content[insert_pos:]
    
    # Add footer navigation before closing body
    if 'footer-navigation' not in content:
        # Find where to insert footer (before last closing divs)
        footer_insert = content.rfind('        <div style="text-align: center;')
        if footer_insert != -1:
            content = content[:footer_insert] + footer_nav + '\n\n' + content[footer_insert:]
    
    # Write updated content
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Navigation added to {filename}")

def main():
    """Update all HTML files with navigation"""
    print("🔗 Adding Navigation to All HTML Documents...")
    print("=" * 60)
    
    # Documents to update (excluding COMPLETE_V4_V5_MODEL_ANALYSIS.html which is already done)
    documents = [
        ('COMPLETE_MODEL_SPECIFICATIONS.html', 'Complete Model Specifications', 'specifications'),
        ('TECHNICAL_IMPLEMENTATION_GUIDE.html', 'Technical Implementation Guide', 'implementation'),
        ('PHASE_BASED_DETAILED_ANALYSIS.html', 'Phase-Based Detailed Analysis', 'phase_analysis')
    ]
    
    for filename, title, category in documents:
        try:
            update_html_file(filename, title, category)
        except Exception as e:
            print(f"  ❌ Error updating {filename}: {e}")
    
    print("\n✅ Navigation integration complete!")
    print("🔗 All HTML documents now have comprehensive navigation")

if __name__ == "__main__":
    main()
