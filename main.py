"""
CSC111 Project 2: Main Module

项目入口，串联整个 pipeline：
1. 读取 bird_metadata.csv，提取唯一物种信息
2. 构建 taxonomy tree（分类学树）
3. 利用 RecordingData 提取每个物种的声音特征
4. 计算所有物种两两之间的 taxonomy distance 和 vocalization similarity
5. 可视化结果

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
import csv

from classes import TaxonomyTree, Species, RecordingData
from sound_analysis import (
    features_to_vector,
    normalize_features,
    cosine_similarity
)
from visualization import draw_scatter_static, draw_scatter_interactive


###############################################################################
# 常量
###############################################################################
API_DATA_FILE = 'bird_data/bird_metadata.csv'
TAXONOMY_INFORMATION = 'bird_data/bird_taxonomy.csv'


###############################################################################
# Step 1: 读取 metadata，构建物种信息
###############################################################################
def build_species_info(metadata_file: str) -> list[dict[str, str]]:
    """读取 metadata CSV，返回唯一物种记录列表。

    每条记录是一个字典，包含: family, genus, species, latin_name, common_name。

    Preconditions:
        - metadata_file 是有效的 CSV 文件路径
    """
    species_information = []
    existing_species: set[str] = set()

    with open(metadata_file, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)  # 跳过表头
        for row in reader:
            if row[3] not in existing_species:
                existing_species.add(row[3])
                species_information.append({
                    'family': row[0],
                    'genus': row[1],
                    'species': row[2],
                    'latin_name': row[3],
                    'common_name': row[4]
                })

    return species_information


def write_taxonomy_csv(species_information: list[dict[str, str]],
                       output_file: str) -> None:
    """将唯一物种信息写入 CSV 文件，用于构建 taxonomy tree。

    Preconditions:
        - species_information 非空
        - output_file 是有效的可写路径
    """
    fieldnames = ['family', 'genus', 'species', 'latin_name', 'common_name']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(species_information)


###############################################################################
# Step 2: 构建 taxonomy tree
###############################################################################
def build_taxonomy_tree(species_information: list[dict[str, str]]) -> TaxonomyTree:
    """根据物种信息构建 TaxonomyTree。

    树结构: Class -> Order -> Family -> Genus -> Species

    Preconditions:
        - species_information 非空
    """
    taxonomy_tree = TaxonomyTree(
        rank='Class',
        root='Aves',
        subtrees=[TaxonomyTree(rank='Order', root='Passeriformes', subtrees=[])]
    )

    for row in species_information:
        taxonomy_tree.add_species(
            row['family'], row['genus'], row['species'],
            row['latin_name'], row['common_name'],
            RecordingData([])  # 先用空的，后面单独提取特征
        )

    return taxonomy_tree


###############################################################################
# Step 3: 提取特征并构建特征向量字典
###############################################################################
def collect_recording_paths(metadata_file: str) -> dict[str, list[str]]:
    """从 metadata CSV 中收集每个物种的所有录音路径。

    返回字典: latin_name -> [录音文件路径列表]

    Preconditions:
        - metadata_file 是有效的 CSV 文件路径
    """
    species_paths: dict[str, list[str]] = {}

    with open(metadata_file, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)  # 跳过表头
        for row in reader:
            latin_name = row[3]
            path = 'bird_data/' + row[6]
            if latin_name not in species_paths:
                species_paths[latin_name] = []
            species_paths[latin_name].append(path)

    return species_paths


def extract_all_species_features(
    species_paths: dict[str, list[str]]
) -> dict[str, list[float]]:
    """对每个物种创建 RecordingData，提取特征，转换为特征向量。

    返回字典: latin_name -> 特征向量 (list[float])

    Preconditions:
        - species_paths 非空
        - 每个 latin_name 对应的路径列表非空
    """
    species_vectors: dict[str, list[float]] = {}

    for latin_name, paths in species_paths.items():
        print(f'  正在提取 {latin_name} 的特征 ({len(paths)} 个录音)...')
        recording = RecordingData(paths)

        # RecordingData.__init__ 会自动调用 average_features()
        # recording.features 是一个 dict，如 {'mfcc': [...], 'pitch_mean': ..., ...}
        if recording.features and recording.features != {}:
            vector = features_to_vector(recording.features)
            species_vectors[latin_name] = vector
        else:
            print(f'    警告: {latin_name} 没有提取到有效特征，跳过。')

    return species_vectors


###############################################################################
# Step 4: 计算 taxonomy distance + vocalization similarity
###############################################################################
def build_comparison_data(
    taxonomy_tree: TaxonomyTree,
    species_vectors: dict[str, list[float]]
) -> list[dict]:
    """构建用于可视化的比较数据。

    对每一对有特征的物种，计算:
        - taxonomic distance（从 taxonomy tree 获取）
        - vocalization similarity（归一化后的余弦相似度）

    返回字典列表，格式为 visualization.py 期望的:
        {'item1': str, 'item2': str, 'distance': int, 'similarity': float}

    Preconditions:
        - len(species_vectors) >= 2
    """
    # 先归一化，确保各维度贡献均衡
    normalized = normalize_features(species_vectors)
    species_list = sorted(normalized.keys())

    comparison_data = []

    for i in range(len(species_list)):
        for j in range(i + 1, len(species_list)):
            s1 = species_list[i]
            s2 = species_list[j]

            # 从 taxonomy tree 获取分类学距离
            distance = taxonomy_tree.get_distance_between(s1, s2)

            if distance is not None:
                similarity = cosine_similarity(normalized[s1], normalized[s2])

                comparison_data.append({
                    'item1': s1.replace('_', ' '),
                    'item2': s2.replace('_', ' '),
                    'distance': distance,
                    'similarity': round(similarity, 4)
                })

    return comparison_data


###############################################################################
# 主函数
###############################################################################
def run_project() -> None:
    """运行整个项目 pipeline:
    1. 读取 metadata → 2. 构建 tree → 3. 提取特征 → 4. 两两比较 → 5. 可视化
    """
    # Step 1: 读取 metadata
    print('Step 1: 读取鸟类 metadata...')
    species_information = build_species_info(API_DATA_FILE)
    write_taxonomy_csv(species_information, TAXONOMY_INFORMATION)
    print(f'  共找到 {len(species_information)} 个唯一物种。')

    # Step 2: 构建 taxonomy tree
    print('Step 2: 构建 taxonomy tree...')
    taxonomy_tree = build_taxonomy_tree(species_information)
    print('  Taxonomy tree 构建完成。')

    # Step 3: 提取声音特征
    print('Step 3: 提取声音特征（可能需要几分钟）...')
    species_paths = collect_recording_paths(API_DATA_FILE)
    species_vectors = extract_all_species_features(species_paths)
    print(f'  成功提取了 {len(species_vectors)} 个物种的特征。')

    # Step 4: 计算两两比较
    print('Step 4: 计算 pairwise distance 和 similarity...')
    comparison_data = build_comparison_data(taxonomy_tree, species_vectors)
    print(f'  共计算了 {len(comparison_data)} 对物种比较。')

    # Step 5: 可视化
    print('Step 5: 生成可视化...')
    draw_scatter_interactive(comparison_data)
    # 如果也想要静态图，取消注释下面这行:
    # draw_scatter_static(comparison_data)

    print('完成！')


if __name__ == '__main__':
    run_project()
