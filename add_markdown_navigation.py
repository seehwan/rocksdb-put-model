#!/usr/bin/env python3
"""
Add navigation links to Markdown documents
"""

def create_markdown_navigation(current_doc, category):
    """Create navigation section for Markdown documents"""
    
    nav_section = """
---

## 📚 Document Navigation

### Main Documents
| Document | Description | Formats |
|----------|-------------|---------|
| 🎯 **Complete V4/V5 Model Analysis** | Comprehensive comparison with dual-structure theory | [📄 MD](COMPLETE_V4_V5_MODEL_ANALYSIS.md) \\| [🌐 HTML](COMPLETE_V4_V5_MODEL_ANALYSIS.html) |
| 🔬 **Complete Model Specifications** | Detailed algorithms, mathematics, and internal mechanisms | [📄 MD](COMPLETE_MODEL_SPECIFICATIONS.md) \\| [🌐 HTML](COMPLETE_MODEL_SPECIFICATIONS.html) |
| 🔧 **Technical Implementation Guide** | Production-ready code and deployment guide | [📄 MD](TECHNICAL_IMPLEMENTATION_GUIDE.md) \\| [🌐 HTML](TECHNICAL_IMPLEMENTATION_GUIDE.html) |
| 📈 **Phase-Based Detailed Analysis** | In-depth analysis of Initial, Middle, and Final phases | [📄 MD](PHASE_BASED_DETAILED_ANALYSIS.md) \\| [🌐 HTML](PHASE_BASED_DETAILED_ANALYSIS.html) |

### Quick Links
"""
    
    # Category-specific quick links
    if category == 'analysis':
        nav_section += """
**📊 For Model Understanding:**
- [🔬 Model Internals](COMPLETE_MODEL_SPECIFICATIONS.md) - Detailed algorithms and mathematics
- [📈 Phase Analysis](PHASE_BASED_DETAILED_ANALYSIS.md) - Phase-by-phase detailed analysis

**🛠️ For Implementation:**
- [🔧 Implementation Guide](TECHNICAL_IMPLEMENTATION_GUIDE.md) - Production-ready code
- [🏠 Main Page](index.html) - Project overview
"""
    elif category == 'specifications':
        nav_section += """
**📊 For Context:**
- [🎯 Main Analysis](COMPLETE_V4_V5_MODEL_ANALYSIS.md) - Overall model comparison
- [📈 Phase Details](PHASE_BASED_DETAILED_ANALYSIS.md) - Phase-specific analysis

**🛠️ For Implementation:**
- [🔧 Production Code](TECHNICAL_IMPLEMENTATION_GUIDE.md) - Implementation guide
- [🏠 Main Page](index.html) - Project overview
"""
    elif category == 'implementation':
        nav_section += """
**📊 For Understanding:**
- [🎯 Model Analysis](COMPLETE_V4_V5_MODEL_ANALYSIS.md) - Model comparison and theory
- [🔬 Model Internals](COMPLETE_MODEL_SPECIFICATIONS.md) - Detailed algorithms

**📈 For Details:**
- [📈 Phase Analysis](PHASE_BASED_DETAILED_ANALYSIS.md) - Phase-specific optimization
- [🏠 Main Page](index.html) - Project overview
"""
    elif category == 'phase_analysis':
        nav_section += """
**📊 For Context:**
- [🎯 Main Analysis](COMPLETE_V4_V5_MODEL_ANALYSIS.md) - Overall model comparison
- [🔬 Model Internals](COMPLETE_MODEL_SPECIFICATIONS.md) - Detailed algorithms

**🛠️ For Implementation:**
- [🔧 Production Code](TECHNICAL_IMPLEMENTATION_GUIDE.md) - Implementation guide
- [🏠 Main Page](index.html) - Project overview
"""
    
    nav_section += """
### 📊 Performance Visualizations
- [📊 V4 vs V5 Performance Comparison](v4_v5_performance_comparison.png) - Overall performance and efficiency
- [🔄 Dual-Structure Analysis](dual_structure_analysis.png) - Phase-A vs Phase-B breakdown  
- [📈 Phase Evolution Analysis](phase_analysis.png) - Performance evolution patterns
- [🧪 Experimental Validation](experimental_validation.png) - 120-minute experiment results

### 🏠 Project Resources
- [🏠 Main Page](index.html) - Project overview and model cards
- [📄 README](README.md) - Quick start and summary
- [📁 Project Structure](FINAL_PROJECT_STRUCTURE.md) - File organization
- [📊 Legacy Models](models.html) - Historical model development

---
"""
    
    return nav_section

def update_markdown_file(filename, current_title, category):
    """Update Markdown file with navigation"""
    
    print(f"📄 Updating {filename}...")
    
    # Read current file
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create navigation
    navigation = create_markdown_navigation(current_title, category)
    
    # Add navigation before the final section
    if '## 📚 Document Navigation' not in content:
        # Find where to insert (before conclusion or last section)
        insert_patterns = [
            '## Conclusion',
            '---\n\n*Analysis completed:',
            '*Document version:',
            '*Implementation Guide completed:',
            '*Phase analysis completed:'
        ]
        
        insert_pos = -1
        for pattern in insert_patterns:
            pos = content.find(pattern)
            if pos != -1:
                insert_pos = pos
                break
        
        if insert_pos != -1:
            content = content[:insert_pos] + navigation + '\n' + content[insert_pos:]
        else:
            # Fallback: add at the end
            content = content + '\n' + navigation
    
    # Write updated content
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Navigation added to {filename}")

def main():
    """Update all Markdown files with navigation"""
    print("🔗 Adding Navigation to All Markdown Documents...")
    print("=" * 60)
    
    # Documents to update
    documents = [
        ('COMPLETE_V4_V5_MODEL_ANALYSIS.md', 'Complete V4/V5 Model Analysis', 'analysis'),
        ('COMPLETE_MODEL_SPECIFICATIONS.md', 'Complete Model Specifications', 'specifications'),
        ('TECHNICAL_IMPLEMENTATION_GUIDE.md', 'Technical Implementation Guide', 'implementation'),
        ('PHASE_BASED_DETAILED_ANALYSIS.md', 'Phase-Based Detailed Analysis', 'phase_analysis')
    ]
    
    for filename, title, category in documents:
        try:
            update_markdown_file(filename, title, category)
        except Exception as e:
            print(f"  ❌ Error updating {filename}: {e}")
    
    print("\n✅ Markdown navigation integration complete!")
    print("🔗 All documents now have comprehensive cross-references")

if __name__ == "__main__":
    main()
