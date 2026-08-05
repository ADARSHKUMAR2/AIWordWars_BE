from langgraph.graph import StateGraph, END
from services.ai_word_generator.graph.nodes import (
    generate_word_node,
    scramble_word_node,
    generate_hint_node
)
from services.ai_word_generator.graph.nodes import WordGeneratorState

def create_word_generator_graph():
    """Create the LangGraph workflow for word generation"""
    
    # Initialize the graph
    workflow = StateGraph(WordGeneratorState)
    
    # Add nodes
    workflow.add_node("generate_word", generate_word_node)
    workflow.add_node("scramble_word", scramble_word_node)
    workflow.add_node("generate_hint", generate_hint_node)
    
    # Define edges (workflow sequence)
    workflow.set_entry_point("generate_word")
    workflow.add_edge("generate_word", "scramble_word")
    workflow.add_edge("scramble_word", "generate_hint")
    workflow.add_edge("generate_hint", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app
