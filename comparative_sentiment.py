"""
Comparative Sentiment Analysis Module

This module provides provider-aware comparative sentiment postprocessing
for cloud provider sentiment analysis results.
"""

import pandas as pd
from typing import Dict, List, Tuple, Any
import numpy as np
from statistics import mean, stdev


def calculate_provider_rankings(results: Dict[str, Dict[str, List[Dict]]]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate provider rankings for each aspect based on sentiment scores.
    
    Args:
        results: Nested dictionary with structure {provider: {aspect: [sentiment_data]}}
        
    Returns:
        Dictionary with rankings and comparative metrics for each aspect
    """
    aspect_rankings = {}
    
    # Get all aspects from the first provider
    if not results:
        return aspect_rankings
    
    first_provider = next(iter(results.keys()))
    aspects = results[first_provider].keys()
    
    for aspect in aspects:
        provider_scores = {}
        
        # Calculate sentiment scores for each provider in this aspect
        for provider in results:
            opinions = results[provider][aspect]
            if not opinions:
                provider_scores[provider] = {
                    'sentiment_score': 0.0,
                    'positive_ratio': 0.0,
                    'negative_ratio': 0.0,
                    'total_opinions': 0,
                    'avg_confidence': 0.0
                }
                continue
                
            total = len(opinions)
            positive = sum(1 for op in opinions if op['sentiment'] == 'Positive')
            negative = sum(1 for op in opinions if op['sentiment'] == 'Negative')
            
            # Calculate sentiment score (positive ratio - negative ratio)
            pos_ratio = positive / total if total > 0 else 0
            neg_ratio = negative / total if total > 0 else 0
            sentiment_score = pos_ratio - neg_ratio
            
            avg_confidence = mean([op['confidence'] for op in opinions]) if opinions else 0.0
            
            provider_scores[provider] = {
                'sentiment_score': sentiment_score,
                'positive_ratio': pos_ratio,
                'negative_ratio': neg_ratio,
                'total_opinions': total,
                'avg_confidence': avg_confidence
            }
        
        # Rank providers by sentiment score
        ranked_providers = sorted(
            provider_scores.items(),
            key=lambda x: x[1]['sentiment_score'],
            reverse=True
        )
        
        aspect_rankings[aspect] = {
            'provider_scores': provider_scores,
            'ranked_providers': ranked_providers,
            'best_provider': ranked_providers[0][0] if ranked_providers else None,
            'worst_provider': ranked_providers[-1][0] if ranked_providers else None
        }
    
    return aspect_rankings


def calculate_overall_provider_rankings(aspect_rankings: Dict[str, Dict[str, Any]]) -> List[Tuple[str, float]]:
    """
    Calculate overall provider rankings across all aspects.
    
    Args:
        aspect_rankings: Results from calculate_provider_rankings
        
    Returns:
        List of (provider, overall_score) tuples sorted by score
    """
    if not aspect_rankings:
        return []
    
    # Get all providers
    first_aspect = next(iter(aspect_rankings.values()))
    providers = first_aspect['provider_scores'].keys()
    
    overall_scores = {}
    
    for provider in providers:
        aspect_scores = []
        total_opinions = 0
        
        for aspect_data in aspect_rankings.values():
            provider_data = aspect_data['provider_scores'][provider]
            aspect_scores.append(provider_data['sentiment_score'])
            total_opinions += provider_data['total_opinions']
        
        # Weight by total opinions to give more weight to providers with more data
        if aspect_scores:
            weighted_score = mean(aspect_scores) * min(1.0, total_opinions / 100.0)
            overall_scores[provider] = weighted_score
    
    return sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)


def generate_comparative_insights(aspect_rankings: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Generate text insights from comparative analysis.
    
    Args:
        aspect_rankings: Results from calculate_provider_rankings
        
    Returns:
        List of insight strings
    """
    insights = []
    
    if not aspect_rankings:
        return ["No data available for comparative analysis."]
    
    # Find aspects where there are clear winners
    for aspect, data in aspect_rankings.items():
        ranked = data['ranked_providers']
        if len(ranked) < 2:
            continue
            
        best_provider, best_score = ranked[0]
        worst_provider, worst_score = ranked[-1]
        
        best_data = best_score
        worst_data = worst_score
        
        # Only generate insights if there's a meaningful difference
        score_diff = best_data['sentiment_score'] - worst_data['sentiment_score']
        if score_diff > 0.1:  # At least 10% difference
            insights.append(
                f"{aspect.title()}: {best_provider} leads with {best_data['positive_ratio']:.1%} positive sentiment "
                f"vs {worst_provider} at {worst_data['positive_ratio']:.1%}"
            )
    
    # Find most controversial aspects (highest sentiment variance)
    aspect_variances = {}
    for aspect, data in aspect_rankings.items():
        scores = [score_data['sentiment_score'] for _, score_data in data['ranked_providers']]
        if len(scores) > 1:
            aspect_variances[aspect] = stdev(scores) if len(scores) > 1 else 0
    
    if aspect_variances:
        most_controversial = max(aspect_variances.items(), key=lambda x: x[1])
        insights.append(f"Most controversial aspect: {most_controversial[0]} (highest sentiment variance)")
    
    return insights


def create_comparative_summary_dataframe(aspect_rankings: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a comprehensive DataFrame for comparative analysis.
    
    Args:
        aspect_rankings: Results from calculate_provider_rankings
        
    Returns:
        DataFrame with comparative metrics
    """
    rows = []
    
    for aspect, data in aspect_rankings.items():
        for rank, (provider, score_data) in enumerate(data['ranked_providers'], 1):
            rows.append({
                'Aspect': aspect,
                'Provider': provider,
                'Rank': rank,
                'Sentiment_Score': score_data['sentiment_score'],
                'Positive_Ratio': score_data['positive_ratio'],
                'Negative_Ratio': score_data['negative_ratio'],
                'Total_Opinions': score_data['total_opinions'],
                'Avg_Confidence': score_data['avg_confidence'],
                'Is_Best': rank == 1,
                'Is_Worst': rank == len(data['ranked_providers'])
            })
    
    return pd.DataFrame(rows)


def create_provider_comparison_matrix(aspect_rankings: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a matrix showing provider vs aspect sentiment scores.
    
    Args:
        aspect_rankings: Results from calculate_provider_rankings
        
    Returns:
        DataFrame with providers as rows and aspects as columns
    """
    if not aspect_rankings:
        return pd.DataFrame()
    
    # Get all providers from first aspect
    first_aspect = next(iter(aspect_rankings.values()))
    providers = list(first_aspect['provider_scores'].keys())
    aspects = list(aspect_rankings.keys())
    
    matrix_data = {}
    
    for aspect in aspects:
        aspect_scores = {}
        for provider in providers:
            score = aspect_rankings[aspect]['provider_scores'][provider]['sentiment_score']
            aspect_scores[provider] = score
        matrix_data[aspect] = aspect_scores
    
    df = pd.DataFrame(matrix_data, index=providers)
    return df


def postprocess_sentiment_results(results: Dict[str, Dict[str, List[Dict]]]) -> Dict[str, Any]:
    """
    Main postprocessing function that generates all comparative analyses.
    
    Args:
        results: Raw sentiment analysis results
        
    Returns:
        Dictionary containing all comparative analysis results
    """
    # Calculate aspect rankings
    aspect_rankings = calculate_provider_rankings(results)
    
    # Calculate overall rankings
    overall_rankings = calculate_overall_provider_rankings(aspect_rankings)
    
    # Generate insights
    insights = generate_comparative_insights(aspect_rankings)
    
    # Create dataframes
    comparative_df = create_comparative_summary_dataframe(aspect_rankings)
    comparison_matrix = create_provider_comparison_matrix(aspect_rankings)
    
    return {
        'aspect_rankings': aspect_rankings,
        'overall_rankings': overall_rankings,
        'insights': insights,
        'comparative_summary': comparative_df,
        'comparison_matrix': comparison_matrix
    }