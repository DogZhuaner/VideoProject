import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import base64
import io
from typing import Dict, List, Any
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class ScoreVisualizer:
    def __init__(self, score_file: str = None):
        """
        初始化成绩可视化器
        :param score_file: 成绩文件路径
        """
        if score_file is None:
            # 获取当前文件（score_visualizer.py）所在目录的上一级（即MultiModelVideo）
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            score_file = os.path.join(base_dir, "data", "score.csv")
        self.score_file = score_file
        self.score_data = self._load_score_data()

    def _load_score_data(self) -> pd.DataFrame:
        """加载成绩数据"""
        try:
            df = pd.read_csv(self.score_file, encoding='utf-8')
            # 处理knowledge字段，将逗号分隔的知识点拆分为列表
            df['knowledge_list'] = df['knowledge'].apply(
                lambda x: [k.strip() for k in str(x).split(',')] if pd.notna(x) else []
            )
            return df
        except FileNotFoundError:
            print(f"成绩文件 {self.score_file} 不存在")
            return pd.DataFrame()

    def get_score_summary(self) -> Dict[str, Any]:
        """获取成绩统计摘要"""
        if self.score_data.empty:
            return {}

        summary = {
            'total_students': len(self.score_data),
            'score_stats': {
                'mean': round(self.score_data['score'].mean(), 2),
                'max': self.score_data['score'].max(),
                'min': self.score_data['score'].min(),
                'std': round(self.score_data['score'].std(), 2),
                'median': self.score_data['score'].median()
            },
            'knowledge_stats': self._get_knowledge_statistics()
        }

        return summary

    def _get_knowledge_statistics(self) -> Dict[str, Any]:
        """获取知识点统计信息"""
        # 统计每个知识点出现的次数
        knowledge_counts = {}
        for knowledge_list in self.score_data['knowledge_list']:
            for knowledge in knowledge_list:
                if knowledge in knowledge_counts:
                    knowledge_counts[knowledge] += 1
                else:
                    knowledge_counts[knowledge] = 1

        # 按出现次数排序
        sorted_knowledge = sorted(knowledge_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            'total_knowledge_types': len(knowledge_counts),
            'most_common_knowledge': sorted_knowledge[:5] if sorted_knowledge else [],
            'knowledge_distribution': knowledge_counts
        }

    def create_score_distribution_plot(self) -> str:
        """创建成绩分布直方图"""
        if self.score_data.empty:
            return ""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('学生成绩分布图', fontsize=16, fontweight='bold')

        # 成绩分布直方图
        scores = self.score_data['score']
        mean_score = scores.mean()

        ax1.hist(scores, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(mean_score, color='red', linestyle='--', linewidth=2, label=f'均值: {mean_score:.1f}')
        ax1.set_title('成绩分布')
        ax1.set_xlabel('分数')
        ax1.set_ylabel('学生人数')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 成绩箱线图
        ax2.boxplot(scores, patch_artist=True, boxprops=dict(facecolor='lightgreen'))
        ax2.set_title('成绩箱线图')
        ax2.set_ylabel('分数')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # 转换为base64字符串
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        return img_str

    def create_knowledge_analysis_plot(self) -> str:
        """创建知识点分析图"""
        if self.score_data.empty:
            return ""

        # 统计知识点出现次数
        knowledge_counts = {}
        for knowledge_list in self.score_data['knowledge_list']:
            for knowledge in knowledge_list:
                if knowledge in knowledge_counts:
                    knowledge_counts[knowledge] += 1
                else:
                    knowledge_counts[knowledge] = 1

        if not knowledge_counts:
            return ""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('易错知识点分析', fontsize=16, fontweight='bold')

        # 知识点出现次数柱状图
        knowledge_names = list(knowledge_counts.keys())
        knowledge_values = list(knowledge_counts.values())

        bars = ax1.bar(knowledge_names, knowledge_values, color='lightcoral', edgecolor='black')
        ax1.set_title('各知识点易错次数')
        ax1.set_xlabel('知识点')
        ax1.set_ylabel('易错次数')
        ax1.tick_params(axis='x', rotation=45)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                     f'{height}', ha='center', va='bottom')

        # 知识点饼图（前5个）
        top_knowledge = sorted(knowledge_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_knowledge:
            labels = [item[0] for item in top_knowledge]
            sizes = [item[1] for item in top_knowledge]
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax2.set_title('易错知识点占比（前5名）')

        plt.tight_layout()

        # 转换为base64字符串
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        return img_str

    def create_student_knowledge_heatmap(self) -> str:
        """创建学生-知识点热力图"""
        if self.score_data.empty:
            return ""

        # 创建学生-知识点矩阵
        all_knowledge = set()
        for knowledge_list in self.score_data['knowledge_list']:
            all_knowledge.update(knowledge_list)

        if not all_knowledge:
            return ""

        # 创建矩阵
        matrix_data = []
        for _, student in self.score_data.iterrows():
            row = []
            for knowledge in all_knowledge:
                if knowledge in student['knowledge_list']:
                    row.append(1)  # 有该易错知识点
                else:
                    row.append(0)  # 没有该易错知识点
            matrix_data.append(row)

        matrix_df = pd.DataFrame(matrix_data,
                                 index=self.score_data['name'],
                                 columns=list(all_knowledge))

        plt.figure(figsize=(12, 8))
        sns.heatmap(matrix_df, annot=True, cmap='YlOrRd', cbar_kws={'label': '易错知识点'})
        plt.title('学生易错知识点分布热力图', fontsize=16, fontweight='bold')
        plt.xlabel('知识点')
        plt.ylabel('学生姓名')
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()

        # 转换为base64字符串
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        return img_str

    def create_score_knowledge_correlation(self) -> str:
        """创建成绩与知识点相关性分析"""
        if self.score_data.empty:
            return ""

        # 统计每个学生的知识点数量
        self.score_data['knowledge_count'] = self.score_data['knowledge_list'].apply(len)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('成绩与易错知识点关系分析', fontsize=16, fontweight='bold')

        # 成绩与知识点数量散点图
        ax1.scatter(self.score_data['knowledge_count'], self.score_data['score'],
                    alpha=0.7, color='blue', s=100)
        ax1.set_xlabel('易错知识点数量')
        ax1.set_ylabel('成绩')
        ax1.set_title('成绩与易错知识点数量关系')
        ax1.grid(True, alpha=0.3)

        # 添加趋势线
        z = np.polyfit(self.score_data['knowledge_count'], self.score_data['score'], 1)
        p = np.poly1d(z)
        ax1.plot(self.score_data['knowledge_count'], p(self.score_data['knowledge_count']),
                 "r--", alpha=0.8)

        # 成绩分布（按知识点数量分组）
        knowledge_groups = self.score_data.groupby('knowledge_count')['score'].mean()
        ax2.bar(knowledge_groups.index, knowledge_groups.values,
                color='lightgreen', edgecolor='black')
        ax2.set_xlabel('易错知识点数量')
        ax2.set_ylabel('平均成绩')
        ax2.set_title('不同易错知识点数量的平均成绩')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # 转换为base64字符串
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        return img_str

    def get_top_students(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """获取前N名学生信息"""
        if self.score_data.empty:
            return []

        top_students = self.score_data.nlargest(top_n, 'score')
        result = []

        for _, student in top_students.iterrows():
            result.append({
                'rank': len(result) + 1,
                'sno': student['sno'],
                'name': student['name'],
                'score': student['score'],
                'knowledge_count': len(student['knowledge_list']),
                'knowledge_list': student['knowledge_list']
            })
            # 为了保持向后兼容性，同时保留student_id键
            result[-1]['student_id'] = result[-1]['sno']

        return result

    def get_knowledge_analysis(self) -> Dict[str, Any]:
        """获取知识点分析数据"""
        if self.score_data.empty:
            return {}

        # 统计知识点
        knowledge_counts = {}
        for knowledge_list in self.score_data['knowledge_list']:
            for knowledge in knowledge_list:
                if knowledge in knowledge_counts:
                    knowledge_counts[knowledge] += 1
                else:
                    knowledge_counts[knowledge] = 1

        # 按出现次数排序
        sorted_knowledge = sorted(knowledge_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            'total_knowledge_types': len(knowledge_counts),
            'most_common_knowledge': sorted_knowledge[:10],
            'knowledge_distribution': knowledge_counts,
            'average_knowledge_per_student': self.score_data['knowledge_list'].apply(len).mean()
        }


# 使用示例
if __name__ == "__main__":
    visualizer = ScoreVisualizer()

    # 获取成绩摘要
    summary = visualizer.get_score_summary()
    print("成绩摘要:", summary)

    # 获取前5名学生
    top_students = visualizer.get_top_students(5)
    print("前5名学生:", top_students)

    # 获取知识点分析
    knowledge_analysis = visualizer.get_knowledge_analysis()
    print("知识点分析:", knowledge_analysis)