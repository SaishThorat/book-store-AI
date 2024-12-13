import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd

# Define paths
base_path = r"./Dataset/"
model_route = r"./Models/"

# Set environment variables
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
os.environ['TORCH_USE_CUDA_DSA'] = '1'

# Define the collaborative filtering model
class CollaborativeFilteringModel(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim, hidden_dim):
        super().__init__()
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        self.hidden_layer = nn.Linear(embedding_dim * 2, hidden_dim)
        self.relu = nn.ReLU()
        self.output_layer = nn.Linear(hidden_dim, 1)

    def forward(self, user_indices, item_indices):
        user_embedded = self.user_embedding(user_indices)
        item_embedded = self.item_embedding(item_indices)
        concatenated = torch.cat([user_embedded, item_embedded], dim=1)
        hidden_output = self.relu(self.hidden_layer(concatenated))
        output = self.output_layer(hidden_output)
        return output

    def get_similar_titles(self, input_title_index, top_k=100):
        device = self.item_embedding.weight.device
        input_title_index = torch.tensor([input_title_index], device=device)
        input_title_embedding = self.item_embedding(input_title_index)
        all_title_embeddings = self.item_embedding.weight
        similarities = F.cosine_similarity(input_title_embedding, all_title_embeddings)
        similar_title_indices = torch.argsort(similarities, descending=True)[:top_k]
        similar_titles = [index_to_title[idx.item()] for idx in similar_title_indices]
        return similar_titles

# Define the content-based filtering model
class ContentBasedFilteringModel(nn.Module):
    def __init__(self, num_categories, num_authors, num_titles, embedding_dim):
        super(ContentBasedFilteringModel, self).__init__()
        self.category_embedding = nn.Embedding(num_categories, embedding_dim)
        self.author_embedding = nn.Embedding(num_authors, embedding_dim)
        self.title_embedding = nn.Embedding(num_titles, embedding_dim)
        self.sentiment_linear = nn.Linear(4 * embedding_dim, 1)

    def forward(self, category_indices, author_indices, title_indices, sentiment_scores):
        category_embedded = self.category_embedding(category_indices)
        author_embedded = self.author_embedding(author_indices)
        title_embedded = self.title_embedding(title_indices)
        sentiment_expanded = sentiment_scores.unsqueeze(1).expand_as(category_embedded)
        concatenated = torch.cat([category_embedded, author_embedded, title_embedded, sentiment_expanded], dim=1)
        output = self.sentiment_linear(concatenated)
        return output

def get_collaborative_recommendations(model, title, num_recommendations=100):
    input_title_index = item_to_index[title]
    model.eval()
    with torch.inference_mode():
        similar_titles = model.get_similar_titles(input_title_index, top_k=num_recommendations)
    return similar_titles

def get_content_based_recommendations(content_based_model, collaborative_recommendations):
    title_details = title_sentiment_aggregated.set_index('Title')[['categories', 'authors', 'sentiment_score']].to_dict(orient='index')
    details = [title_details[title] for title in collaborative_recommendations]
    category_indices = torch.tensor([category_to_index[detail['categories']] for detail in details], dtype=torch.long)
    author_indices = torch.tensor([author_to_index[detail['authors']] for detail in details], dtype=torch.long)
    title_indices = torch.tensor([title_to_index[title] for title in collaborative_recommendations], dtype=torch.long)
    sentiment_scores = torch.tensor([detail['sentiment_score'] for detail in details], dtype=torch.float32)
    category_indices, author_indices, title_indices, sentiment_scores = category_indices.to(device), author_indices.to(device), title_indices.to(device), sentiment_scores.to(device)
    content_based_model.eval()
    with torch.inference_mode():
        predictions = content_based_model(category_indices, author_indices, title_indices, sentiment_scores)
    sorted_titles = [title for _, title in sorted(zip(predictions, collaborative_recommendations), reverse=True)]
    return sorted_titles

def partial_name_matching(partial_name, all_books):
    matching_titles = [title for title in all_books if partial_name.lower() in title.lower()]
    unique_matching_titles = list(set(matching_titles))
    if len(unique_matching_titles) == 0:
        return "404", "Invalid !! "
    return unique_matching_titles[0]

def getRecommendation(title, num_recommendations=10):
    global device, item_to_index, index_to_title, model_loaded, cbf_model_loaded, title_sentiment_aggregated,title_sentiment_aggregated, category_to_index, author_to_index, title_to_index
    # Load data
    merged_dataframe_pth = base_path + "merged_dataframe_with_sentiment_labels.csv"
    merged_df = pd.read_csv(merged_dataframe_pth)
    
    # Create mappings
    user_ids = merged_df['User_id'].unique()
    item_ids = merged_df['Title'].unique()
    user_to_index = {user_id: idx for idx, user_id in enumerate(user_ids)}
    item_to_index = {item_id: idx for idx, item_id in enumerate(item_ids)}
    index_to_title = {idx: title for title, idx in item_to_index.items()}
    
    # Load models
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = model_route + "collaborative_filtering_model.pth"
    model_loaded = torch.load(model_path, map_location=device)
    model_loaded.to(device)
    model_path = model_route + "content_based_filtering_model.pth"
    cbf_model_loaded = torch.load(model_path, map_location=device)
    cbf_model_loaded.to(device)
    
    # Prepare data
    title_sentiment_aggregated = merged_df.groupby(['Title', 'authors', 'categories'])['sentiment_score'].mean().reset_index()
    unique_categories = merged_df['categories'].unique()
    unique_authors = merged_df['authors'].unique()
    unique_titles = title_sentiment_aggregated['Title'].unique()
    
    category_to_index = {category: idx for idx, category in enumerate(unique_categories)}
    author_to_index = {author: idx for idx, author in enumerate(unique_authors)}
    title_to_index = {title: idx for idx, title in enumerate(unique_titles)}
    
    # Process recommendation
    input_title = partial_name_matching(title, merged_df['Title'])
    
    collaborative_recommendations = get_collaborative_recommendations(model_loaded, input_title, num_recommendations)
    recommendations = get_content_based_recommendations(cbf_model_loaded, collaborative_recommendations)

    res = {"recommendations": {f'R{i}': recommendations[i] for i in range(len(recommendations))}}
    print(res)
    return res