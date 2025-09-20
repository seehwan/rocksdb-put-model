#!/usr/bin/env python3
"""
Document Navigation System Generator
Creates comprehensive navigation links between all project documents
"""

import os
from pathlib import Path

class DocumentNavigationGenerator:
    """Generate navigation links for all project documents"""
    
    def __init__(self, project_root="/home/sslab/rocksdb-put-model"):
        self.project_root = Path(project_root)
        
        # Document structure mapping
        self.document_structure = {
            'main_documents': [
                {
                    'title': 'Complete V4/V5 Model Analysis',
                    'files': ['COMPLETE_V4_V5_MODEL_ANALYSIS.md', 'COMPLETE_V4_V5_MODEL_ANALYSIS.html'],
                    'description': 'Comprehensive comparison with dual-structure theory',
                    'icon': '🎯',
                    'category': 'analysis'
                },
                {
                    'title': 'Complete Model Specifications', 
                    'files': ['COMPLETE_MODEL_SPECIFICATIONS.md', 'COMPLETE_MODEL_SPECIFICATIONS.html'],
                    'description': 'Detailed algorithms, mathematics, and internal mechanisms',
                    'icon': '🔬',
                    'category': 'specifications'
                },
                {
                    'title': 'Technical Implementation Guide',
                    'files': ['TECHNICAL_IMPLEMENTATION_GUIDE.md', 'TECHNICAL_IMPLEMENTATION_GUIDE.html'],
                    'description': 'Production-ready code and deployment guide',
                    'icon': '🔧',
                    'category': 'implementation'
                },
                {
                    'title': 'Phase-Based Detailed Analysis',
                    'files': ['PHASE_BASED_DETAILED_ANALYSIS.md', 'PHASE_BASED_DETAILED_ANALYSIS.html'],
                    'description': 'In-depth analysis of Initial, Middle, and Final phases',
                    'icon': '📈',
                    'category': 'phase_analysis'
                }
            ],
            'visualizations': [
                {
                    'title': 'V4 vs V5 Performance Comparison',
                    'file': 'v4_v5_performance_comparison.png',
                    'description': 'Overall performance and information efficiency comparison'
                },
                {
                    'title': 'Dual-Structure Analysis',
                    'file': 'dual_structure_analysis.png', 
                    'description': 'Phase-A physical vs Phase-B software degradation'
                },
                {
                    'title': 'Phase Evolution Analysis',
                    'file': 'phase_analysis.png',
                    'description': 'Performance evolution across operational phases'
                },
                {
                    'title': 'Experimental Validation',
                    'file': 'experimental_validation.png',
                    'description': '120-minute FillRandom experiment validation'
                }
            ],
            'supporting_documents': [
                {
                    'title': 'Project Structure',
                    'file': 'FINAL_PROJECT_STRUCTURE.md',
                    'description': 'Clean project organization after optimization'
                }
            ]
        }
    
    def generate_navigation_header(self, current_doc_title):
        """Generate navigation header for documents"""
        
        nav_html = """
        <div class="document-navigation">
            <div class="nav-header">
                <h4>📚 Document Navigation</h4>
                <p>Complete RocksDB Put-Rate Model Documentation</p>
            </div>
            <div class="nav-grid">
"""
        
        # Add main documents
        for doc in self.document_structure['main_documents']:
            is_current = current_doc_title in doc['title']
            current_class = ' current-doc' if is_current else ''
            
            nav_html += f"""
                <div class="nav-card{current_class}">
                    <div class="nav-icon">{doc['icon']}</div>
                    <h5>{doc['title']}</h5>
                    <p>{doc['description']}</p>
                    <div class="nav-links">
"""
            
            for file in doc['files']:
                if file.endswith('.md'):
                    nav_html += f'                        <a href="{file}">📄 Markdown</a>\n'
                else:
                    nav_html += f'                        <a href="{file}">🌐 HTML</a>\n'
            
            nav_html += """
                    </div>
                </div>
"""
        
        nav_html += """
            </div>
        </div>
"""
        
        return nav_html
    
    def generate_quick_links(self, current_category):
        """Generate quick links section"""
        
        quick_links = """
        <div class="quick-links">
            <h4>🔗 Quick Navigation</h4>
            <div class="links-grid">
"""
        
        # Category-specific recommendations
        if current_category == 'analysis':
            quick_links += """
                <div class="link-group">
                    <h5>📊 For Model Understanding</h5>
                    <a href="COMPLETE_MODEL_SPECIFICATIONS.html">🔬 Model Internals</a>
                    <a href="PHASE_BASED_DETAILED_ANALYSIS.html">📈 Phase Analysis</a>
                </div>
                <div class="link-group">
                    <h5>🛠️ For Implementation</h5>
                    <a href="TECHNICAL_IMPLEMENTATION_GUIDE.html">🔧 Implementation</a>
                    <a href="index.html">🏠 Main Page</a>
                </div>
"""
        elif current_category == 'specifications':
            quick_links += """
                <div class="link-group">
                    <h5>📊 For Context</h5>
                    <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🎯 Main Analysis</a>
                    <a href="PHASE_BASED_DETAILED_ANALYSIS.html">📈 Phase Details</a>
                </div>
                <div class="link-group">
                    <h5>🛠️ For Implementation</h5>
                    <a href="TECHNICAL_IMPLEMENTATION_GUIDE.html">🔧 Production Code</a>
                    <a href="index.html">🏠 Main Page</a>
                </div>
"""
        elif current_category == 'implementation':
            quick_links += """
                <div class="link-group">
                    <h5>📊 For Understanding</h5>
                    <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🎯 Model Analysis</a>
                    <a href="COMPLETE_MODEL_SPECIFICATIONS.html">🔬 Model Internals</a>
                </div>
                <div class="link-group">
                    <h5>📈 For Details</h5>
                    <a href="PHASE_BASED_DETAILED_ANALYSIS.html">📈 Phase Analysis</a>
                    <a href="index.html">🏠 Main Page</a>
                </div>
"""
        elif current_category == 'phase_analysis':
            quick_links += """
                <div class="link-group">
                    <h5>📊 For Context</h5>
                    <a href="COMPLETE_V4_V5_MODEL_ANALYSIS.html">🎯 Main Analysis</a>
                    <a href="COMPLETE_MODEL_SPECIFICATIONS.html">🔬 Model Internals</a>
                </div>
                <div class="link-group">
                    <h5>🛠️ For Implementation</h5>
                    <a href="TECHNICAL_IMPLEMENTATION_GUIDE.html">🔧 Production Code</a>
                    <a href="index.html">🏠 Main Page</a>
                </div>
"""
        
        quick_links += """
            </div>
        </div>
"""
        
        return quick_links
    
    def generate_visualization_gallery(self):
        """Generate visualization gallery for all documents"""
        
        gallery_html = """
        <div class="visualization-gallery">
            <h4>📊 Performance Visualizations</h4>
            <div class="viz-grid">
"""
        
        for viz in self.document_structure['visualizations']:
            gallery_html += f"""
                <div class="viz-card">
                    <img src="{viz['file']}" alt="{viz['title']}" loading="lazy">
                    <h5>{viz['title']}</h5>
                    <p>{viz['description']}</p>
                </div>
"""
        
        gallery_html += """
            </div>
        </div>
"""
        
        return gallery_html
    
    def generate_footer_navigation(self):
        """Generate footer navigation for all documents"""
        
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
        </div>
"""
        
        return footer_nav
    
    def generate_navigation_css(self):
        """Generate CSS for navigation components"""
        
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
        
        .nav-header p {
            margin: 0;
            color: #6c757d;
            font-style: italic;
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
            cursor: pointer;
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
        
        /* Quick Links */
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
        
        .link-group a:hover {
            text-decoration: underline;
        }
        
        /* Visualization Gallery */
        .visualization-gallery {
            background: #e8f5e8;
            border-radius: 10px;
            padding: 25px;
            margin: 30px 0;
        }
        
        .visualization-gallery h4 {
            margin: 0 0 20px 0;
            color: #155724;
            text-align: center;
        }
        
        .viz-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .viz-card {
            background: white;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        
        .viz-card img {
            width: 100%;
            height: auto;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .viz-card h5 {
            margin: 0 0 5px 0;
            color: #2c3e50;
            font-size: 0.95em;
        }
        
        .viz-card p {
            margin: 0;
            color: #6c757d;
            font-size: 0.8em;
        }
        
        /* Footer Navigation */
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
        
        .footer-section li {
            margin: 6px 0;
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
        }
        
        /* Breadcrumb Navigation */
        .breadcrumb {
            background: #f8f9fa;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 20px 0;
            font-size: 0.9em;
        }
        
        .breadcrumb a {
            color: #007bff;
            text-decoration: none;
        }
        
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        
        .breadcrumb span {
            color: #6c757d;
            margin: 0 8px;
        }
        
        /* Related Documents */
        .related-documents {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 20px;
            margin: 30px 0;
        }
        
        .related-documents h4 {
            margin: 0 0 15px 0;
            color: #1565c0;
        }
        
        .related-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 12px;
        }
        
        .related-item {
            background: white;
            padding: 12px;
            border-radius: 5px;
            border: 1px solid #bbdefb;
        }
        
        .related-item h6 {
            margin: 0 0 5px 0;
            color: #2c3e50;
            font-size: 0.9em;
        }
        
        .related-item p {
            margin: 0 0 8px 0;
            color: #6c757d;
            font-size: 0.8em;
        }
        
        .related-item a {
            color: #007bff;
            text-decoration: none;
            font-size: 0.85em;
        }
        
        .related-item a:hover {
            text-decoration: underline;
        }
"""
        
        return nav_css

def main():
    """Generate navigation system for all documents"""
    print("🔗 Generating Document Navigation System...")
    print("=" * 60)
    
    generator = DocumentNavigationGenerator()
    
    # Generate navigation CSS
    nav_css = generator.generate_navigation_css()
    
    # Update each HTML document with navigation
    documents_to_update = [
        ('COMPLETE_V4_V5_MODEL_ANALYSIS.html', 'Complete V4/V5 Model Analysis', 'analysis'),
        ('COMPLETE_MODEL_SPECIFICATIONS.html', 'Complete Model Specifications', 'specifications'),
        ('TECHNICAL_IMPLEMENTATION_GUIDE.html', 'Technical Implementation Guide', 'implementation'),
        ('PHASE_BASED_DETAILED_ANALYSIS.html', 'Phase-Based Detailed Analysis', 'phase_analysis')
    ]
    
    for filename, title, category in documents_to_update:
        print(f"📄 Updating {filename}...")
        
        # Generate navigation components
        nav_header = generator.generate_navigation_header(title)
        quick_links = generator.generate_quick_links(category)
        viz_gallery = generator.generate_visualization_gallery()
        footer_nav = generator.generate_footer_navigation()
        
        # Save navigation components for manual insertion
        nav_file = f"navigation_components_{category}.html"
        with open(nav_file, 'w') as f:
            f.write("<!-- Navigation CSS -->\n")
            f.write(f"<style>\n{nav_css}\n</style>\n\n")
            f.write("<!-- Navigation Header -->\n")
            f.write(nav_header)
            f.write("\n<!-- Quick Links -->\n")
            f.write(quick_links)
            f.write("\n<!-- Visualization Gallery -->\n")
            f.write(viz_gallery)
            f.write("\n<!-- Footer Navigation -->\n")
            f.write(footer_nav)
        
        print(f"  ✅ Navigation components saved to {nav_file}")
    
    print("\n✅ Navigation system generation complete!")
    print("📁 Navigation components generated for manual integration")
    
    return nav_css

if __name__ == "__main__":
    main()
