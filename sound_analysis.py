"""
CSC111 Project 2: Sound Analysis Module

这个模块负责声音特征的相似度计算，包括：
- 将 RecordingData 的特征字典转为特征向量
- Z-score 归一化（防止某些特征因数值范围大而主导计算）
- Cosine similarity 计算
- 所有物种两两之间的相似度比较

特征提取部分由 classes.py 中的 RecordingData 完成，
本模块只处理提取后的数据。

Copyright (c) 2026 Lucy Wang, Yiming Xu, Ted Song. All rights reserved.
"""
from __future__ import annotations
import math


###############################################################################
# 特征向量转换
###############################################################################
def features_to_vector(features: dict) -> list[float]:
    """将 RecordingData.features 字典转换为有序的特征向量，用于计算相似度。

    向量顺序为: mfcc[0..n] + pitch_mean + centroid_mean + bandwidth_mean + rms_mean

    Preconditions:
        - features != {}
        - 'mfcc' in features
        - all(k in features for k in ['pitch_mean', 'centroid_mean', 'bandwidth_mean', 'rms_mean'])
    """
    vector = list(features['mfcc'])
    vector.append(features['pitch_mean'])
    vector.append(features['centroid_mean'])
    vector.append(features['bandwidth_mean'])
    vector.append(features['rms_mean'])
    return vector


###############################################################################
# 相似度计算
###############################################################################
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """计算两个特征向量之间的余弦相似度。

    余弦相似度衡量两个向量之间的夹角，返回值在 -1 到 1 之间。
    值越接近 1 表示两个向量越相似。

    Preconditions:
        - len(vec_a) == len(vec_b)
        - len(vec_a) > 0
    """
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def euclidean_distance(vec_a: list[float], vec_b: list[float]) -> float:
    """计算两个特征向量之间的欧几里得距离。

    距离越小说明两个物种的叫声越相似。

    Preconditions:
        - len(vec_a) == len(vec_b)
        - len(vec_a) > 0
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec_a, vec_b)))


###############################################################################
# Z-score 归一化
###############################################################################
def normalize_features(species_vectors: dict[str, list[float]]) -> dict[str, list[float]]:
    """对所有物种的特征向量进行 Z-score 归一化。

    每个特征维度都会被标准化为均值为 0、标准差为 1。
    这样可以防止数值范围大的特征（如 pitch，单位是 Hz）
    压过数值范围小的特征（如 MFCC 系数）。

    Preconditions:
        - len(species_vectors) > 0
        - 所有向量长度一致
    """
    species_list = list(species_vectors.keys())
    vectors = [species_vectors[s] for s in species_list]
    num_features = len(vectors[0])
    num_species = len(vectors)

    # 计算每个特征维度的均值和标准差
    means = []
    stds = []
    for i in range(num_features):
        values = [vectors[j][i] for j in range(num_species)]
        mean_val = sum(values) / num_species
        variance = sum((v - mean_val) ** 2 for v in values) / num_species
        std_val = math.sqrt(variance) if variance > 0 else 1.0
        means.append(mean_val)
        stds.append(std_val)

    # 归一化
    normalized = {}
    for s in species_list:
        vec = species_vectors[s]
        normalized[s] = [(vec[i] - means[i]) / stds[i] for i in range(num_features)]

    return normalized


###############################################################################
# 两两相似度计算
###############################################################################
def compute_all_pairwise_similarities(
    species_vectors: dict[str, list[float]]
) -> list[tuple[str, str, float]]:
    """计算所有物种两两之间的余弦相似度。

    先进行 Z-score 归一化，再计算 cosine similarity。
    返回一个列表，每个元素是 (species1, species2, similarity)，
    按相似度从高到低排序。

    Preconditions:
        - len(species_vectors) >= 2
    """
    normalized = normalize_features(species_vectors)

    species_list = sorted(normalized.keys())
    results = []

    for i in range(len(species_list)):
        for j in range(i + 1, len(species_list)):
            s1 = species_list[i]
            s2 = species_list[j]
            sim = cosine_similarity(normalized[s1], normalized[s2])
            results.append((s1, s2, sim))

    results.sort(key=lambda x: x[2], reverse=True)
    return results


###############################################################################
# Main block
###############################################################################
if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['math'],
        'max-line-length': 120
    })
