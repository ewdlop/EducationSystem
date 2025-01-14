import spacy
import html
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import re

@dataclass
class GrammaticalFeature:
    """Stores detailed grammatical information"""
    text: str
    pos: str
    dep: str
    tag: str
    morph: Dict[str, str]
    is_stop: bool
    lemma: str

class AdvancedGrammarHighlighter:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        
        # Extended color scheme
        self.pos_colors = {
            'NOUN': '#FF4444',      # Red
            'PROPN': '#FF6666',     # Light Red
            'VERB': '#4444FF',      # Blue
            'AUX': '#6666FF',       # Light Blue
            'ADJ': '#44AA44',       # Green
            'ADV': '#AA44AA',       # Purple
            'DET': '#AAAAAA',       # Gray
            'ADP': '#999999',       # Dark Gray
            'CCONJ': '#888888',     # Conjunctions
            'SCONJ': '#777777',     # Subordinating conj
            'PRON': '#FF8844',      # Orange
            'NUM': '#44AAAA',       # Cyan
            'PUNCT': '#000000',     # Black
            'INTJ': '#FF44FF',      # Pink
            'SYM': '#44FFFF',       # Light Cyan
            'PART': '#BBBBBB',      # Light Gray
        }
        
        # Dependency relations colors
        self.dep_colors = {
            'nsubj': '#FF0000',     # Subject
            'dobj': '#0000FF',      # Direct object
            'iobj': '#00FF00',      # Indirect object
            'amod': '#FF00FF',      # Adjective modifier
            'advmod': '#00FFFF',    # Adverb modifier
            'ROOT': '#000000',      # Root
        }
        
        # Common grammar patterns
        self.grammar_patterns = {
            'passive_voice': r'\b(am|is|are|was|were)\s+\w+ed\b',
            'run_on': r'[^.!?]+(?:,\s*and|,\s*but)\s+[^.!?]+(?:,\s*and|,\s*but)\s+[^.!?]+',
            'double_negative': r'\b(?:not|never|no|nobody|nothing|nowhere)\b.*\b(?:not|never|no|nobody|nothing|nowhere)\b',
        }
        
        # Grammar rules
        self.grammar_rules = {
            'subject_verb_agreement': self._check_subject_verb_agreement,
            'article_usage': self._check_article_usage,
            'pronoun_agreement': self._check_pronoun_agreement,
        }

    def analyze_text(self, text: str) -> Dict:
        """Comprehensive text analysis"""
        doc = self.nlp(text)
        
        analysis = {
            'tokens': self._analyze_tokens(doc),
            'sentences': self._analyze_sentences(doc),
            'dependencies': self._analyze_dependencies(doc),
            'patterns': self._find_patterns(text),
            'grammar_checks': self._check_grammar(doc),
            'statistics': self._generate_statistics(doc)
        }
        
        return analysis

    def _analyze_tokens(self, doc) -> List[GrammaticalFeature]:
        """Analyze individual tokens"""
        return [
            GrammaticalFeature(
                text=token.text,
                pos=token.pos_,
                dep=token.dep_,
                tag=token.tag_,
                morph=dict(token.morph),
                is_stop=token.is_stop,
                lemma=token.lemma_
            )
            for token in doc
        ]

    def _analyze_sentences(self, doc) -> List[Dict]:
        """Analyze sentence structure"""
        return [{
            'text': sent.text,
            'root': sent.root.text,
            'subject': next((token.text for token in sent 
                           if token.dep_ == 'nsubj'), None),
            'verb': next((token.text for token in sent 
                         if token.pos_ == 'VERB'), None),
            'objects': [token.text for token in sent 
                       if token.dep_ in ('dobj', 'iobj')],
        } for sent in doc.sents]

    def _analyze_dependencies(self, doc) -> List[Dict]:
        """Analyze syntactic dependencies"""
        return [{
            'source': token.text,
            'target': token.head.text,
            'relation': token.dep_,
            'source_pos': token.pos_,
            'target_pos': token.head.pos_
        } for token in doc if token.dep_ != 'punct']

    def _find_patterns(self, text: str) -> Dict[str, List[str]]:
        """Find grammar patterns"""
        matches = {}
        for pattern_name, pattern in self.grammar_patterns.items():
            matches[pattern_name] = re.findall(pattern, text, re.IGNORECASE)
        return matches

    def _check_grammar(self, doc) -> Dict[str, List[str]]:
        """Check grammar rules"""
        issues = {}
        for rule_name, check_func in self.grammar_rules.items():
            issues[rule_name] = check_func(doc)
        return issues

    def _check_subject_verb_agreement(self, doc) -> List[str]:
        """Check subject-verb agreement"""
        issues = []
        for sent in doc.sents:
            subject = next((token for token in sent if token.dep_ == 'nsubj'), None)
            verb = next((token for token in sent if token.pos_ == 'VERB'), None)
            
            if subject and verb:
                subj_num = subject.morph.get('Number', [''])[0]
                verb_num = verb.morph.get('Number', [''])[0]
                if subj_num and verb_num and subj_num != verb_num:
                    issues.append(f"Agreement issue: '{subject.text}' ({subj_num}) with '{verb.text}' ({verb_num})")
        return issues

    def _check_article_usage(self, doc) -> List[str]:
        """Check article usage"""
        issues = []
        for token in doc:
            if token.pos_ == 'DET' and token.text.lower() in ('a', 'an'):
                next_word = token.nbor() if token.i + 1 < len(doc) else None
                if next_word:
                    if token.text.lower() == 'a' and next_word.text[0].lower() in 'aeiou':
                        issues.append(f"Use 'an' before '{next_word.text}'")
                    elif token.text.lower() == 'an' and next_word.text[0].lower() not in 'aeiou':
                        issues.append(f"Use 'a' before '{next_word.text}'")
        return issues

    def _check_pronoun_agreement(self, doc) -> List[str]:
        """Check pronoun agreement"""
        issues = []
        for token in doc:
            if token.pos_ == 'PRON':
                antecedent = self._find_antecedent(token)
                if antecedent:
                    pron_num = token.morph.get('Number', [''])[0]
                    ant_num = antecedent.morph.get('Number', [''])[0]
                    if pron_num and ant_num and pron_num != ant_num:
                        issues.append(f"Pronoun agreement issue: '{token.text}' with '{antecedent.text}'")
        return issues

    def _find_antecedent(self, pronoun) -> Optional[spacy.tokens.Token]:
        """Find pronoun antecedent"""
        for token in reversed(list(pronoun.doc[:pronoun.i])):
            if token.pos_ in ('NOUN', 'PROPN'):
                return token
        return None

    def _generate_statistics(self, doc) -> Dict:
        """Generate text statistics"""
        return {
            'token_count': len(doc),
            'sentence_count': len(list(doc.sents)),
            'pos_distribution': self._count_pos(doc),
            'avg_sentence_length': len(doc) / len(list(doc.sents)) if doc else 0,
            'vocabulary_richness': len(set(token.lemma_ for token in doc)) / len(doc) if doc else 0
        }

    def _count_pos(self, doc) -> Dict[str, int]:
        """Count parts of speech"""
        counts = {}
        for token in doc:
            counts[token.pos_] = counts.get(token.pos_, 0) + 1
        return counts

    def generate_html(self, text: str) -> str:
        """Generate interactive HTML visualization"""
        analysis = self.analyze_text(text)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .text-analysis {{
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }}
                .token {{
                    display: inline-block;
                    margin: 2px;
                    padding: 2px 4px;
                    border-radius: 3px;
                    cursor: help;
                }}
                .grammar-issues {{
                    background-color: #fff3f3;
                    padding: 10px;
                    margin: 10px 0;
                    border-left: 4px solid #ff4444;
                }}
                .statistics {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 10px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                }}
            </style>
            <script>
                function showTokenInfo(info) {{
                    document.getElementById('token-info').innerHTML = info;
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <h1>Grammar Analysis</h1>
                
                <div class="text-analysis">
                    {self._generate_highlighted_text(analysis)}
                </div>
                
                <div id="token-info"></div>
                
                <div class="grammar-issues">
                    <h2>Grammar Issues</h2>
                    {self._generate_issues_html(analysis)}
                </div>
                
                <div class="statistics">
                    {self._generate_statistics_html(analysis)}
                </div>
                
                <div class="dependencies">
                    <h2>Syntactic Dependencies</h2>
                    {self._generate_dependencies_html(analysis)}
                </div>
            </div>
        </body>
        </html>
        """
        return html_content

    def _generate_highlighted_text(self, analysis: Dict) -> str:
        """Generate highlighted text with tooltips"""
        result = []
        for token in analysis['tokens']:
            color = self.pos_colors.get(token.pos, '#000000')
            info = (f"POS: {token.pos}<br>"
                   f"Dependency: {token.dep}<br>"
                   f"Lemma: {token.lemma}<br>"
                   f"Morphology: {token.morph}")
            
            result.append(
                f'<span class="token" style="color: {color}" '
                f'onmouseover="showTokenInfo(\'{info}\')">'
                f'{html.escape(token.text)}</span>'
            )
            
        return ' '.join(result)

    def _generate_issues_html(self, analysis: Dict) -> str:
        """Generate HTML for grammar issues"""
        issues = []
        for rule, rule_issues in analysis['grammar_checks'].items():
            if rule_issues:
                issues.extend(
                    f'<li><strong>{rule}:</strong> {issue}</li>'
                    for issue in rule_issues
                )
        
        return f'<ul>{"".join(issues) if issues else "<li>No issues found.</li>"}</ul>'

    def _generate_statistics_html(self, analysis: Dict) -> str:
        """Generate HTML for statistics"""
        stats = analysis['statistics']
        return ''.join(
            f'<div class="stat-card">'
            f'<strong>{key}:</strong> {value}'
            f'</div>'
            for key, value in stats.items()
        )

    def _generate_dependencies_html(self, analysis: Dict) -> str:
        """Generate HTML for dependencies"""
        deps = analysis['dependencies']
        return ''.join(
            f'<div>{dep["source"]} →{dep["relation"]}→ {dep["target"]}</div>'
            for dep in deps
        )

# Example usage
if __name__ == "__main__":
    highlighter = AdvancedGrammarHighlighter()
    
    # Test text
    text = """The quick brown fox jumps over the lazy dog. 
              She have been running fast. 
              An user wrote a excellent story."""
    
    # Generate analysis
    html_output = highlighter.generate_html(text)
    
    # Save to file
    with open('grammar_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
