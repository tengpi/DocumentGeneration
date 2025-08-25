import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Fieldschema:
    """Schema definition for data fields"""
    name: str
    category: str
    description: str
    is_multi_select: bool = False


class SchemaParser:
    """Schema parser for parsing data schema files and formatting customer data"""
    
    def __init__(self, schema_file_path: str = None):
        self.schema: Dict[str, Fieldschema]= {}
        self.categories = {
            '基礎信息':'Basic Information',
            '互動與偏好':'Interaction & Preferences',
            '財務数據':'Financial Data',
            '交易行為':'Transaction Behavior',
            '風險評估':'Risk Assessment'
        }

        if schema_file_path:
            self.load_schema(schema_file_path)

    def load_schema(self, schema_file_path: str):
        """Load schema definition from file"""
        try:
            with open(schema_file_path, 'r', encoding='utf-8')as f:
                content = f.read()
            self.parse_schema(content)
        except Exception as e:
            print(f"Error loading schema file: {e}")

    def parseschema(self, schema_content: str):
        """Parse schema content"""
        lines = schema_content.strip().split('\n')

        for line in lines:
            if ':' in line:
                # Parse field name and description
                parts = line.split(':', 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    description_part = parts[1].strip()

                    # Parse category and description
                    if ',' in description_part:
                        category_desc = description_part.split(',',1)
                        category = category_desc[0].strip()
                        description = category_desc[1].strip() if len(category_desc)> 1 else ''

                        # Check if it's a multi-select field
                        is_multi_select ='【多選】'in description
                        if is_multi_select:
                            description = description.replace('【多選】', '').stríp()
                        
                        # Create field schema
                        self.schema[field_name]= Fieldschema(
                            name=field_name,
                            category=category,
                            description=description,
                            is_multi_select=is_multi_select
                        )
                            
    def parsecsv_data(self, csv_content: str) -> Dict[str, Any]:
        """Parse customer data in CSV format"""
        lines = csv_content.strip().split('\n')
        if len(lines)< 2:
            return {}

        headers = lines[0].split(',')
        values = lines[1].split(',')

        # Create data dictionary
        data_dict = {}
        for i,header in enumerate(headers):
            if i < len(values):
                value = values[i].strip()
                # Handle empty values
                if value == '' or value.lower()== 'nan':
                    value = None
                data_dict[header.strip()]= value

        return data_dict
    
    def categorize_data(self, data_dict: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Organize data by categories"""
        categorized = {}

        for field_name, value in data_dict.items():
            if field_name in self.schema:
                field_schema = self.schema[field_name]
                category = field_schema.category

                if category not in categorized:
                    categorized[category]={}

                categorized[category][field_name]= {
                    'value': value,
                    'description': field_schema.description,
                    'is_multi_select': field_schema.is_multi_select
                }

        return categorized

    def format_customer_data_section(self, csv_content: str, include_insights: bool = True) -> str:
        """Format customer data into readable sections"""
        # Parse CSV data
        data_dict = self.parse_csv_data(csv_content)

        #Organize data by categories
        categorized_data = self.categorize_data(data_dict)

        # Build output
        sections = ["Customer Data Analysis:\n"]

        # Output categories in predefined order
        category_order = ['基礎信息','互動與偏好','財務数據','交易行為','風險評估']
                          
        for category in category_order:
            if category in categorized_data:
                # Add category title(Chinese-English)
                english_category = self.categories.get(category, category)
                sections.append(f"\n{category}({english_category}):")

                # Add field information
                for field_name, field_info in categorized_data[category].items():
                    value = field_info['value']
                    description = field_info['description']

                    # Format value display
                    formatted_value = self._format_value(field_name, value)

                    # Build line
                    line = f"- {field_name} ({description}): {formatted_value}"
                    sections.append(line)

        # Add key insights
        if include_insights:
            insights = self._generate_key_insights(data_dict)
            sections.append("\n\nKEY INSIGHTS TO CONSIDER:")
            for i,insight in enumerate(insights,1):
                sections.append(f"{i}. {insight}")

        return '\n'.join(sections)
    
    def _format_value(self,field_name: str,value: Any)-> str:
        """Format field value display"""
        if value is None:
            return "N/A"
        
        # Value mappings for special fields
        value_mappings = {
            'Y':'是(Yes)',
            'N':'否(No)',
            'Male':'男性',
            'Female':'女性',
            'Single':'單身',
            'Married':'已婚'
        }

        # Use mapping if value exists in mappings
        if str(value) in value_mappings:
            return f"{value}({value_mappings[str(value)]})"
        
        return str(value)
    
    def _generate_key_insights(self, data_dict: Dict[str, Any])-> List[str]:
        """Generate key insights based on customer data"""
        insights = []

        # Age and life stage insights
        age_group = data_dict.get('age_group','')
        life_stage = data_dict.get('life_stage','')
        if age_group and life_stage:
            insights.append(f"{life_stage} in age group {age_group}")
        
        # Financial status insights
        trb_range = data_dict.get('trb_range', '')
        allocation_cash = data_dict.get('allocation_cash','')
        allocation_inv = data_dict.get('allocation_inv', '')
        if trb_range and allocation_cash:
            insights.append(f"Total wealth {trb_range} with {allocation_cash} cash allocation")
            if allocation_inv == '0.00%':
                insights.append("No investment products held despite significant wealth - opportunity for portfolio diversification")

        #Transaction behavior insights
        trans_security = data_dict.get("trans security",'')
        hldg_INV = data_dict.get('hldg INV', "")
        if trans_security and trans_security != '0' and hldg_INV == 'N':
            insights.append(f"Active in securities trading ({trans_security} transactions) but no investment products held")

        #Risk rating insights
        rpq_level = data_dict.get('rpq_level','')
        if rpq_level:
            risk_descriptions ={
                "1":"Conservative",
                "2":"Conservative to Moderate",
                "3":"Moderate",
                "4":"Moderate to Aggressive",
                "5":"Aggressive"
            }
            risk_desc = risk_descriptions.get(str(rpq_level), f'Level {rpq_level}')
            insights.append(f"Risk profile: {risk_desc}")

        # Special situation insights
        child = data_dict.get('child', '')
        ms = data_dict.get('MS','')
        if child == 'Y' and ms == 'Single':
            insights.append("single parent with children - may need education planning and protection products")

        # Goal insights
        fhc_goal_type = data_dict.get('fhc_goal_type','')
        if fhc_goal_type:
            insights.append(f"Financial goal: {fhc_goal_type}")

        return insights
    
    def get_field_description(self, field_name: str) -> str:
        """Get field description"""
        if field_name in self.schema:
            return self.schema[field_name].description
        return ""
    
    def get_field_category(self, field_name: str)-> str:
        """Get field category"""
        if field_name in self.schema:
            return self.schema[field_name].category
        return ""


        