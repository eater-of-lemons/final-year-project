import json
import plotly.express as px
import pandas as pd

class ReelVisualizer:
    """creates visualization of reel data"""
    
    def __init__(self):
        """set file paths"""
        self.input_file = '../data/demo-stuff/demo-vader-analysis-filtered.json'
        self.output_file = '../data/demo-stuff/demo-interactive-plot-filtered.html'
    
    def prepare_data(self):
        """load and prepare data for plotting"""
        with open(self.input_file, 'r') as f:
            data = json.load(f)
        
        plot_data = []
        for video_id, video_info in data.items():
            likes = int(video_info['likes'].replace(',', ''))
            compound_sentiment = video_info['avg_sentiment']['compound']
            
            plot_data.append({
                'video_id': video_id,
                'url': video_info['url'],
                'likes': likes,
                'compound_sentiment': compound_sentiment,
                'comments_count': video_info['comments_count']
            })
        
        return pd.DataFrame(plot_data)
    
    def create_plot(self, df):
        """create plotly scatter plot"""
        fig = px.scatter(
            df,
            x='compound_sentiment',
            y='likes',
            hover_data=['url'],
            title='likes vs sentiment',
            labels={
                'compound_sentiment': 'average sentiment',
                'likes': 'number of likes'
            }
        )
        
        fig.update_traces(
            marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')),
            selector=dict(mode='markers')
        )
        
        fig.update_layout(
            hovermode='closest',
            yaxis_type="log",
            yaxis=dict(
                title='likes (log scale)',
                tickvals=[1000, 10000, 100000, 1000000],
                ticktext=['1k', '10k', '100k', '1m']
            ),
            xaxis=dict(title='sentiment (higher = more positive)'),
            plot_bgcolor='rgba(240,240,240,0.9)',
            height=800,
            width=1400
        )
        
        fig.update_traces(
            hovertemplate="<br>".join([
                "sentiment: %{x}",
                "likes: %{y}",
                "url: %{customdata[0]}"
            ])
        )
        
        return fig
    
    def save_plot(self, fig):
        """save plot as interactive html"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    {plot_div}
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const plot = document.getElementById('{plot_id}');
            plot.on('plotly_click', function(data) {{
                const url = data.points[0].customdata[0];
                window.open(url, '_blank');
            }});
        }});
    </script>
</body>
</html>
"""
        
        fig.write_html(
            self.output_file,
            full_html=False,
            include_plotlyjs='cdn',
            div_id='plot'
        )
        
        with open(self.output_file, "r") as f:
            plot_content = f.read()
        
        final_html = html_template.format(
            plot_div=plot_content,
            plot_id="plot"
        )
        
        with open(self.output_file, "w") as f:
            f.write(final_html)
    
    def run_visualization(self):
        """main function to create visualization"""
        df = self.prepare_data()
        fig = self.create_plot(df)
        self.save_plot(fig)
        print(f"saved plot to {self.output_file}")

if __name__ == "__main__":
    visualizer = ReelVisualizer()
    visualizer.run_visualization()