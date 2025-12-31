"""
GEMA-RAG v2.3 - Knowledge Graph Construction
Section 6: Entity & Relationship Extraction (Rule-based)
✅ FIXED: All path issues resolved for src/ execution
"""

import json
import re
from pathlib import Path
from collections import defaultdict


class KnowledgeGraphBuilder:
    """Build knowledge graph from chunks using rule-based extraction"""
    
    def __init__(self, chunks_path='../data/parsed/chunks.jsonl'):  # ✅ FIXED
        self.chunks = []
        print("Loading chunks...")
        with open(chunks_path, 'r', encoding='utf-8') as f:
            for line in f:
                self.chunks.append(json.loads(line))
        print(f"✓ Loaded {len(self.chunks)} chunks\n")
        
        self.entities = defaultdict(list)
        self.relationships = []
        
        # Predefined entities
        self.known_policies = [
            'Startup India Seed Fund Scheme', 'SISFS', 'Fund of Funds',
            'DPIIT Recognition', 'Section 80-IAC', 'Angel Tax Exemption',
            'Startup India', 'Atal Innovation Mission', 'Make in India'
        ]
        
        self.known_organizations = [
            'DPIIT', 'Department for Promotion of Industry and Internal Trade',
            'SIDBI', 'Small Industries Development Bank of India',
            'NITI Aayog', 'Ministry of Commerce', 'Government of India'
        ]
        
        self.known_sectors = [
            'Technology', 'Fintech', 'Edtech', 'Healthtech', 'Agritech',
            'E-commerce', 'SaaS', 'Agriculture', 'Manufacturing', 'Healthcare',
            'Education', 'Logistics', 'CleanTech', 'FoodTech', 'MarineTech'
        ]
        
        self.known_investors = [
            'Sequoia Capital', 'Accel Partners', 'Blume Ventures',
            'Matrix Partners', 'Lightspeed', 'Nexus Venture Partners',
            'Tiger Global', 'SoftBank', 'Kalaari Capital'
        ]
    
    def extract_entities(self):
        """Extract entities from chunks using rule-based matching"""
        print("Extracting entities...")
        
        entity_types = {
            'POLICY': [],
            'ORGANIZATION': [],
            'AMOUNT': [],
            'SECTOR': [],
            'INVESTOR': []
        }
        
        processed = 0
        for chunk in self.chunks:
            text = chunk['text']
            text_lower = text.lower()
            
            # Extract policies
            for policy in self.known_policies:
                if policy.lower() in text_lower:
                    entity_types['POLICY'].append({
                        'name': policy,
                        'chunk_id': chunk['chunk_id'],
                        'source': chunk['filename'],
                        'page': chunk['page']
                    })
            
            # Extract organizations
            for org in self.known_organizations:
                if org.lower() in text_lower:
                    entity_types['ORGANIZATION'].append({
                        'name': org,
                        'chunk_id': chunk['chunk_id'],
                        'source': chunk['filename'],
                        'page': chunk['page']
                    })
            
            # Extract sectors
            for sector in self.known_sectors:
                if sector.lower() in text_lower:
                    entity_types['SECTOR'].append({
                        'name': sector,
                        'chunk_id': chunk['chunk_id'],
                        'source': chunk['filename'],
                        'page': chunk['page']
                    })
            
            # Extract investors
            for investor in self.known_investors:
                if investor.lower() in text_lower:
                    entity_types['INVESTOR'].append({
                        'name': investor,
                        'chunk_id': chunk['chunk_id'],
                        'source': chunk['filename'],
                        'page': chunk['page']
                    })
            
            # Extract amounts from canonicals
            if chunk.get('canonicals') and 'amount_surface' in chunk['canonicals']:
                entity_types['AMOUNT'].append({
                    'value': chunk['canonicals']['amount_surface'],
                    'normalized': chunk['canonicals'].get('amount_inr'),
                    'chunk_id': chunk['chunk_id'],
                    'source': chunk['filename'],
                    'page': chunk['page']
                })
            
            # Extract amounts from text
            amount_patterns = [
                r'Rs\.?\s*(\d+(?:,\d+)*)\s*(Lakhs?|Crores?|lakh|crore)',
                r'\$\s*(\d+(?:,\d+)*)\s*(M|B|Million|Billion)?',
                r'INR\s*(\d+(?:,\d+)*)\s*(Lakhs?|Crores?)?'
            ]
            
            for pattern in amount_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_types['AMOUNT'].append({
                        'value': match.group(0),
                        'chunk_id': chunk['chunk_id'],
                        'source': chunk['filename'],
                        'page': chunk['page']
                    })
            
            processed += 1
            if processed % 2000 == 0:
                print(f"  Processed {processed}/{len(self.chunks)} chunks...")
        
        # Deduplicate entities
        for ent_type, entities in entity_types.items():
            unique = {}
            for ent in entities:
                key = ent.get('name') or ent.get('value')
                if key and key not in unique:
                    unique[key] = ent
            entity_types[ent_type] = list(unique.values())
        
        self.entities = entity_types
        
        print(f"\n✓ Extracted entities:")
        for ent_type, ents in entity_types.items():
            print(f"  - {ent_type}: {len(ents)}")
        
        return entity_types
    
    def extract_relationships(self):
        """Extract relationships between entities"""
        print("\nExtracting relationships...")
        
        relationships = []
        
        # Relationship patterns
        patterns = [
            (r'(SISFS|Seed Fund|Startup India).*(?:provides?|offers?).*(?:Rs\.?\s*\d+\s*(?:Lakhs?|Crores?))', 'PROVIDES_FUNDING', 'POLICY', 'AMOUNT'),
            (r'(DPIIT|Department).*(?:manages?|administers?).*(?:Startup India|SISFS)', 'MANAGES', 'ORGANIZATION', 'POLICY'),
            (r'eligible.*for.*(SISFS|Seed Fund|Recognition)', 'ELIGIBLE_FOR', 'STARTUP', 'POLICY'),
            (r'(sector-agnostic|all sectors|supports.*sectors)', 'SUPPORTS_SECTORS', 'POLICY', 'SECTOR'),
            (r'(\w+)\s+(?:invested|funded)\s+(?:in|into)\s+(\w+)', 'INVESTED_IN', 'INVESTOR', 'STARTUP'),
            (r'maximum.*(?:grant|investment).*(?:Rs\.?\s*\d+\s*(?:Lakhs?|Crores?))', 'HAS_LIMIT', 'POLICY', 'AMOUNT')
        ]
        
        for chunk in self.chunks:
            text = chunk['text']
            
            # Pattern matching for relationships
            for pattern, rel_type, source_type, target_type in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    relationships.append({
                        'type': rel_type,
                        'source_type': source_type,
                        'target_type': target_type,
                        'text': match.group(0)[:150],  # First 150 chars
                        'chunk_id': chunk['chunk_id'],
                        'source': chunk['filename'],
                        'page': chunk['page']
                    })
        
        # Deduplicate relationships
        unique_rels = {}
        for rel in relationships:
            key = (rel['type'], rel['text'][:50])
            if key not in unique_rels:
                unique_rels[key] = rel
        
        self.relationships = list(unique_rels.values())
        print(f"✓ Extracted {len(self.relationships)} relationships\n")
        
        return self.relationships
    
    def build_graph(self):
        """Build the complete knowledge graph"""
        print("="*80)
        print("🏗️  Building Knowledge Graph...")
        print("="*80 + "\n")
        
        # Extract entities and relationships
        entities = self.extract_entities()
        relationships = self.extract_relationships()
        
        # Create graph structure
        graph = {
            'entities': entities,
            'relationships': relationships,
            'stats': {
                'total_entities': sum(len(v) for v in entities.values()),
                'total_relationships': len(relationships),
                'entity_types': len(entities),
                'policy_count': len(entities['POLICY']),
                'organization_count': len(entities['ORGANIZATION']),
                'sector_count': len(entities['SECTOR']),
                'amount_count': len(entities['AMOUNT']),
                'investor_count': len(entities['INVESTOR'])
            }
        }
        
        # Save graph - ✅ FIXED PATH & MKDIR
        output_path = Path('../data/knowledge_graph')
        output_path.mkdir(exist_ok=True, parents=True)  # ✅ FIXED
        
        with open(output_path / 'graph.json', 'w', encoding='utf-8') as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        
        print("="*80)
        print("✅ Knowledge Graph Built Successfully")
        print("="*80)
        print(f"Total Entities: {graph['stats']['total_entities']}")
        print(f"  - Policies: {graph['stats']['policy_count']}")
        print(f"  - Organizations: {graph['stats']['organization_count']}")
        print(f"  - Sectors: {graph['stats']['sector_count']}")
        print(f"  - Amounts: {graph['stats']['amount_count']}")
        print(f"  - Investors: {graph['stats']['investor_count']}")
        print(f"\nTotal Relationships: {graph['stats']['total_relationships']}")
        print(f"\nSaved to: {output_path / 'graph.json'}")
        print("="*80 + "\n")
        
        return graph


if __name__ == '__main__':
    builder = KnowledgeGraphBuilder()
    graph = builder.build_graph()
    
    # Display sample entities
    print("\n📊 Sample Entities:\n")
    for ent_type, entities in graph['entities'].items():
        if entities:
            print(f"{ent_type}:")
            for ent in entities[:5]:  # Show first 5
                name = ent.get('name') or ent.get('value')
                print(f"  - {name}")
            print()
    
    # Display sample relationships
    if graph['relationships']:
        print("\n🔗 Sample Relationships:\n")
        for rel in graph['relationships'][:5]:
            print(f"  [{rel['type']}] {rel['text'][:80]}...")
