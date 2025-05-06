import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio

# === Step 1: 读取并预处理数据 ===
df = pd.read_csv("your_data.csv")  # 替换为你的CSV文件路径
df = df.dropna(subset=["smiles_0", "smiles_1"])

# 分组 - 包含condition_0作为分组依据
unique_combinations = df[['smiles_0', 'smiles_1', 'condition_0']].drop_duplicates().reset_index(drop=True)
unique_combinations['group'] = range(1, len(unique_combinations) + 1)
df = df.merge(unique_combinations, on=['smiles_0', 'smiles_1', 'condition_0'], how='left')

# 构建 customdata
df['customdata'] = df[['group', 'smiles_0', 'smiles_1', 'concentration_0', 'concentration_1', 'condition_0', 'y_true_0', 'y_pred_0']].to_dict('records')

# === Step 2: 创建图 ===
scatter = go.Scatter(
    x=df['y_true_0'],
    y=df['y_pred_0'],
    mode='markers',
    marker=dict(color='blue', size=8),
    customdata=df['customdata'],
    hoverinfo='none',  # 禁用默认悬停信息
    name="Data"
)

ideal_line = go.Scatter(
    x=[-1, 55],
    y=[-1, 55],
    mode='lines',
    line=dict(dash='dash', color='black'),
    name="y = x"
)

# 设置8:6的宽高比
layout = go.Layout(
    title="Viscosity",
    xaxis=dict(title="y_true_0", range=[-1, 55]),
    yaxis=dict(title="y_pred_0", range=[-1, 55]),
    hovermode='closest',
    width=1200,   # 增加宽度以容纳侧面板
    height=800,  # 设置高度为600像素 (8:6比例)
    margin=dict(l=50, r=50, t=80, b=50)  # 设置边距
)

fig = go.Figure(data=[scatter, ideal_line], layout=layout)

# === Step 3: 生成带自定义 JS 和侧面板的 HTML ===
html_body = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

# 创建HTML结构和样式
# 创建HTML结构，对CSS中的大括号进行转义
html_structure = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Interactive R² Plot</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .container {{
            display: flex;
            width: 100%;
        }}
        .plot-container {{
            flex: 3;
        }}
        .info-panel {{
            flex: 1;
            margin-left: 20px;
            padding: 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #f9f9f9;
            height: 700px;
            overflow-y: auto;
        }}
        .info-panel h3 {{
            margin-top: 0;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }}
        .info-item {{
            margin-bottom: 5px;
        }}
        .value-display {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .highlight {{
            background-color: #ffeb3b;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .group-info {{
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin-top: 15px;
            border-left: 4px solid #1976d2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="plot-container">
            {plot_div}
        </div>
        <div class="info-panel" id="info-panel">
            <h3>数据点信息</h3>
            <p>将鼠标悬停在图表上的点以查看详细信息</p>
            <div class="group-info">
                <div class="info-item">组: <span id="group-value" class="value-display">-</span></div>
                <div class="info-item">条件 (温度): <span id="cond0-value" class="value-display">-</span></div>
            </div>
            <div id="point-info">
                <div class="info-item">真实值: <span id="true-value" class="value-display">-</span></div>
                <div class="info-item">预测值: <span id="pred-value" class="value-display">-</span></div>
                <div class="info-item">第一个组分SMILES: <span id="smiles0-value" class="value-display">-</span></div>
                <div class="info-item">第二个组分SMILES: <span id="smiles1-value" class="value-display">-</span></div>
                <div class="info-item">第一个组分浓度: <span id="conc0-value" class="value-display">-</span></div>
                <div class="info-item">第二个组分浓度: <span id="conc1-value" class="value-display">-</span></div>
            </div>
        </div>
    </div>
    {js_script}
</body>
</html>
"""

# 添加 JS 脚本：hover 时高亮同组点并更新侧面板
js_script = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 等待Plotly图表完全加载
    setTimeout(function() {
        const gd = document.querySelector('.js-plotly-plot');
        let hoverTimer = null;
        let currentHoverPoint = null;
        
        // 获取侧面板元素
        const groupValue = document.getElementById('group-value');
        const trueValue = document.getElementById('true-value');
        const predValue = document.getElementById('pred-value');
        const smiles0Value = document.getElementById('smiles0-value');
        const smiles1Value = document.getElementById('smiles1-value');
        const conc0Value = document.getElementById('conc0-value');
        const conc1Value = document.getElementById('conc1-value');
        const cond0Value = document.getElementById('cond0-value');
        
        gd.on('plotly_hover', function(eventData) {
            if (!eventData.points || eventData.points.length === 0) return;
            
            const point = eventData.points[0];
            // 只有第一个trace(散点图)有分组数据
            if (point.curveNumber !== 0) return;
            
            // 清除之前的定时器
            if (hoverTimer) {
                clearTimeout(hoverTimer);
            }
            
            // 保存当前悬停的点
            currentHoverPoint = point;
            
            // 设置0.25秒延迟后高亮
            hoverTimer = setTimeout(function() {
                const pointData = currentHoverPoint.customdata;
                const hoveredGroup = pointData.group;
                const pointCount = gd.data[0].x.length;
                const colors = [];
                
                // 为每个点设置颜色
                for (let i = 0; i < pointCount; i++) {
                    const thisGroup = gd.data[0].customdata[i].group;
                    if (thisGroup === hoveredGroup) {
                        colors.push('red'); // 同一组的点设为红色
                    } else {
                        colors.push('rgba(200, 200, 200, 0.3)'); // 其他组的点设为透明灰色
                    }
                }
                
                // 更新侧面板信息
                groupValue.textContent = pointData.group;
                trueValue.textContent = pointData.y_true_0.toFixed(4);
                predValue.textContent = pointData.y_pred_0.toFixed(4);
                smiles0Value.textContent = pointData.smiles_0;
                smiles1Value.textContent = pointData.smiles_1;
                conc0Value.textContent = pointData.concentration_0;
                conc1Value.textContent = pointData.concentration_1;
                cond0Value.textContent = pointData.condition_0;
                
                // 高亮显示真实值和预测值
                trueValue.classList.add("highlight");
                predValue.classList.add("highlight");
                
                Plotly.restyle(gd, {'marker.color': [colors]}, [0]);
            }, 250); // 设置250毫秒(0.25秒)的延迟
        });
        
        gd.on('plotly_unhover', function() {
            // 清除定时器
            if (hoverTimer) {
                clearTimeout(hoverTimer);
                hoverTimer = null;
            }
            
            // 移除高亮样式
            trueValue.classList.remove("highlight");
            predValue.classList.remove("highlight");
            
            // 恢复所有点的颜色
            const pointCount = gd.data[0].x.length;
            const colors = Array(pointCount).fill('blue');
            Plotly.restyle(gd, {'marker.color': [colors]}, [0]);
        });
    }, 500); // 给予500ms的时间确保Plotly完全加载
});
</script>
"""

# 合并 HTML
full_html = html_structure.format(plot_div=html_body, js_script=js_script)

# === Step 4: 保存为 HTML 文件 ===
with open("viscosity.html", "w", encoding="utf-8") as f:
    f.write(full_html)

