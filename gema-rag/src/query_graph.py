"""
GEMA-RAG v2.3 - Knowledge Graph Query System
Section 6: Graph-based Relational Queries
✅ FIXED: Path corrected for src/ execution
"""

import json
from pathlib import Path


class GraphQueryEngine:
    """Query the knowledge graph for relational information"""
    
    def __init__(self, graph_path='../data/knowledge_graph/graph.json'):
        print("Loading knowledge graph...")
        with open(graph_path, 'r', encoding='utf-8') as f:
            self.graph = json.load(f)
        
        self.entities = self.graph['entities']
        self.relationships = self.graph['relationships']
        
        print(f"✓ Graph loaded: {self.graph['stats']['total_entities']} entities, "
              f"{self.graph['stats']['total_relationships']} relationships\n")
    
    def query_by_entity_type(self, entity_type):
        """Get all entities of a specific type"""
        return self.entities.get(entity_type.upper(), [])
    
    def query_relationships_by_type(self, rel_type):
        """Get all relationships of a specific type"""
        return [r for r in self.relationships if r['type'] == rel_type]
    
    def find_entity(self, entity_name, entity_type=None):
        """Find a specific entity by name"""
        entity_name_lower = entity_name.lower()
        results = []
        
        # Search in specific type or all types
        types_to_search = [entity_type.upper()] if entity_type else self.entities.keys()
        
        for ent_type in types_to_search:
            for entity in self.entities.get(ent_type, []):
                name = entity.get('name') or entity.get('value')
                if name and entity_name_lower in name.lower():
                    results.append({
                        'type': ent_type,
                        'entity': entity
                    })
        
        return results
    
    def get_related_entities(self, entity_name):
        """Find all entities related to a given entity"""
        related = []
        
        for rel in self.relationships:
            if entity_name.lower() in rel['text'].lower():
                related.append(rel)
        
        return related
    
    def answer_graph_query(self, query):
        """
        Answer graph-specific queries using structured data
        """
        query_lower = query.lower()
        
        # Query patterns
        if 'which organizations' in query_lower or 'who manages' in query_lower:
            orgs = self.query_by_entity_type('ORGANIZATION')
            return self._format_entity_list('Organizations', orgs)
        
        elif 'which sectors' in query_lower or 'what sectors' in query_lower:
            sectors = self.query_by_entity_type('SECTOR')
            return self._format_entity_list('Sectors', sectors)
        
        elif 'which policies' in query_lower or 'what schemes' in query_lower:
            policies = self.query_by_entity_type('POLICY')
            return self._format_entity_list('Policies/Schemes', policies)
        
        elif 'which investors' in query_lower or 'who are the investors' in query_lower:
            investors = self.query_by_entity_type('INVESTOR')
            return self._format_entity_list('Investors', investors)
        
        elif 'funding amounts' in query_lower or 'how much funding' in query_lower:
            amounts = self.query_by_entity_type('AMOUNT')[:10]  # Top 10
            return self._format_entity_list('Funding Amounts', amounts)
        
        elif 'relationships' in query_lower:
            return self._format_relationships()
        
        # Entity-specific queries
        elif 'sisfs' in query_lower or 'seed fund' in query_lower:
            return self._get_entity_details('SISFS')
        
        elif 'dpiit' in query_lower:
            return self._get_entity_details('DPIIT')
        
        else:
            return None  # Not a graph query
    
    def _format_entity_list(self, title, entities):
        """Format entity list as answer"""
        if not entities:
            return f"No {title.lower()} found in the knowledge graph."
        
        answer = f"**{title} in the Knowledge Graph:**\n\n"
        for i, entity in enumerate(entities[:15], 1):  # Limit to 15
            name = entity.get('name') or entity.get('value')
            source = entity.get('source', 'Unknown')
            answer += f"{i}. **{name}** (from {source})\n"
        
        if len(entities) > 15:
            answer += f"\n... and {len(entities) - 15} more."
        
        return answer
    
    def _format_relationships(self):
        """Format relationships as answer"""
        if not self.relationships:
            return "No relationships found in the knowledge graph."
        
        answer = f"**Key Relationships in the Knowledge Graph:**\n\n"
        
        # Group by type
        rel_by_type = {}
        for rel in self.relationships:
            rel_type = rel['type']
            if rel_type not in rel_by_type:
                rel_by_type[rel_type] = []
            rel_by_type[rel_type].append(rel)
        
        for rel_type, rels in rel_by_type.items():
            answer += f"\n**{rel_type.replace('_', ' ').title()}:** ({len(rels)} found)\n"
            for rel in rels[:3]:  # Show top 3 per type
                answer += f"  - {rel['text'][:100]}...\n"
        
        return answer
    
    def _get_entity_details(self, entity_name):
        """Get detailed information about a specific entity"""
        results = self.find_entity(entity_name)
        
        if not results:
            return None
        
        answer = f"**Information about {entity_name}:**\n\n"
        
        # Show entity occurrences
        for result in results:
            entity = result['entity']
            name = entity.get('name') or entity.get('value')
            source = entity.get('source', 'Unknown')
            page = entity.get('page', 'N/A')
            
            answer += f"- **Type:** {result['type']}\n"
            answer += f"- **Name:** {name}\n"
            answer += f"- **Source:** {source} (Page {page})\n\n"
        
        # Show related relationships
        related = self.get_related_entities(entity_name)
        if related:
            answer += f"\n**Related Relationships:**\n"
            for rel in related[:5]:
                answer += f"- [{rel['type']}] {rel['text'][:100]}...\n"
        
        return answer


# Test the graph query engine
if __name__ == '__main__':
    engine = GraphQueryEngine()
    
    print("="*80)
    print("🧪 Testing Graph Query System")
    print("="*80 + "\n")
    
    # Test queries
    test_queries = [
        "Which organizations manage startup schemes?",
        "What sectors are covered in the knowledge graph?",
        "Which investors are mentioned?",
        "Tell me about SISFS",
        "Tell me about DPIIT"
    ]
    
    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"Q: {query}")
        print(f"{'─'*80}\n")
        
        answer = engine.answer_graph_query(query)
        if answer:
            print(answer)
        else:
            print("Not a graph query - would use regular RAG")
        
        input("\nPress Enter for next query...")
