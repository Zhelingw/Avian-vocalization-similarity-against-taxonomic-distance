
from __future__ import annotations
from typing import Optional, Any
import librosa
import librosa.feature
import math
from statistics import mean


class TaxonomyTree:
    """
        A taxonomy tree data structure, starting from the class Aves to the species.

        Representation invariants:
            - self._root is not None or self._subtrees == []
            - all taxonomy_trees have a parent, except the root passeriformes of the whole tree
            - self._species is not None and self._root is not None and self._subtrees is None
            or self._species is None and self._root is not None and self._subtrees is not None
            - self._rank in {'class', 'order', 'family', 'genus', 'species'}
    """
    # Private instance attributes:
    # - _rank: the rank the current tree's root represents
    # - _root: Latin name of the taxonomic rank stored at this tree's root, or None if the tree is empty.
    # - _subtrees: The subgroups of this rank, or None if the rank is a species. It is empty when self._root is None.
    # - _parent: The supergroup of this rank.
    # - _species: The species represented by this tree. If the rank is higher than species, then it is Empty.

    _rank: str
    _root: Optional[str]
    _subtrees: Optional[list[TaxonomyTree]]
    _parent: Optional[TaxonomyTree]
    _species: Optional[Species]

    def __init__(
            self,
            rank: str,
            root: Optional[str],
            subtrees: Optional[list[TaxonomyTree]],
            parent: Optional[TaxonomyTree] = None,
            species: Optional[Species] = None
    ) -> None:
        """Initialize the tree and set the parent for each child."""
        self._rank = rank
        self._root = root
        self._subtrees = subtrees
        self._parent = parent
        self._species = species

        # Automatically set the parent of each subtree to be the current tree
        if self._subtrees:
            for subtree in self._subtrees:
                subtree._parent = self

    def get_latin(self) -> str:
        """
        Return the Latin name of the root of the current tree.

        >>> tree.get_latin()
        'Aves'
        """
        return self._root

    def get_rank(self) -> str:
        """
        Return the rank of the root of the current tree.
        >>> tree.get_rank()
        'Class'
        """
        return self._rank

    def get_all_species(self) -> dict[str, TaxonomyTree]:
        """
        Return a mapping of all latin names of each species to its Species tree in the tree.

        >>> all_species = tree.get_all_species()
        >>> [species for species in all_species]
        ['Parus_major', 'Parus_minor']
        """
        if self._species is not None:
            return {self._root: self}
        else:
            species = {}
            for subtree in self._subtrees:
                species.update(subtree.get_all_species())
            return species

    # def get_all_trees_of_rank(self, target_rank: str) -> dict[str, TaxonomyTree]:
    #     """
    #     Return a mapping of all latin names of each node at the required rank to its tree.
    #
    #     Preconditions:
    #     - self._rank in {'class', 'order', 'family', 'genus', 'species'}
    #
    #     >>> all_species = tree.get_all_trees_of_rank('species')
    #     >>> [species for species in all_species]
    #     ['Parus_major', 'Parus_minor']
    #     """
    #     if self._species is not None:
    #         return {self._root: self}
    #     else:
    #         species = {}
    #         for subtree in self._subtrees:
    #             species.update(subtree.get_all_species())
    #         return species

    def get_species(self, latin_name: str) -> TaxonomyTree | None:
        """
        Return the TaxonomyTree object that represents the species corresponding to the latin_name string,
        None if the name is not found.

        >>> tree.get_species('Parus_major').get_latin()
        'Parus_major'
        >>> tree.get_species('Parus_minor').get_latin()
        'Parus_minor'
        >>> tree.get_species('Numenius_tenuirostris') is None
        True
        """
        all_species = self.get_all_species()
        if latin_name in all_species:
            return all_species[latin_name]
        else:
            return None
        # if self._species is not None:
        #     if self._root == latin_name:
        #         return self
        #     else:
        #         return None
        # else:
        #     for tree in self._subtrees:
        #         species = tree.get_species(latin_name)
        #         if species is not None:
        #             return species
        #     return None
        # if latin_name not in self.get_all_species()

    def add_species(
            self,
            family: str,
            genus: str,
            latin_name: str,
            common_name: str,
            recording_datas: RecordingData
    ) -> None:
        """Add in the new species with the given information.

            Preconditions:
            - self._rank == 'class'
            - all the family, genus, species, latin_name, common_name are valid names from the Xeno-Canto API
        """
        order_node = self._get_or_create_child('order', 'Passeriformes')
        family_node = order_node._get_or_create_child('family', family)
        genus_node = family_node._get_or_create_child('genus', genus)
        species = Species(name_latin=latin_name, name_common=common_name, recording_data=recording_datas)
        leaf = TaxonomyTree(rank='species', root=latin_name, subtrees=None, species=species)
        if genus_node._subtrees is None:
            genus_node._subtrees = []
        genus_node._subtrees.append(leaf)

    def _get_or_create_child(self, rank: str, name: str) -> TaxonomyTree:
        """Private helper function that finds the node with the required name,
        or return the new child if it's not already in the tree."""
        if self._subtrees is None:
            self._subtrees = []

        for child in self._subtrees:
            if child._rank == rank and child._root == name:
                return child

        new_child = TaxonomyTree(
            rank=rank,
            root=name,
            subtrees=[],
            parent=self,
            species=None
        )
        self._subtrees.append(new_child)
        return new_child

    def get_distance_between(self, species1: str, species2: str) -> int | None:
        """
        Calculate the taxonomical distance between the two species.

        Preconditions:
        - self.get_all_species()

        >>> tree.get_distance_between('Parus_minor', 'Parus_major')
        1
        >>> tree.get_distance_between('Numenius_tenuirostris', 'Parus_major') is None
        True
        """
        s1_heritage = []
        s1_tracer = self.get_species(species1)
        s2_tracer = self.get_species(species2)
        if s1_tracer is None or s2_tracer is None:
            return None
        while s1_tracer._parent is not None:
            s1_heritage.append(s1_tracer._root)
            s1_tracer = s1_tracer._parent
        distance = 0

        for i in range(len(s1_heritage)):
            if s2_tracer._root == s1_heritage[i]:
                return distance
            distance += 1
            s2_tracer = s2_tracer._parent
        return len(s1_heritage)

    # def get_distance_to(self, other: TaxonomyTree) -> int:
    #     """
    #     Calculate the taxonomical distance between self and other.
    #
    #     Preconditions:
    #     - self._species is not None and other._species is not None
    #
    #     >>> Parus_major.get_distance_to(Parus_minor)
    #     1
    #     """
    #     self_heritage = []
    #     self_tracer = self
    #     while self_tracer._parent is not None:
    #         self_heritage.append(self_tracer._root)
    #         self_tracer = self_tracer._parent
    #     distance = 0
    #     other_tracer = other
    #     for i in range(len(self_heritage)):
    #         if other_tracer._root == self_heritage[i]:
    #             return distance
    #         distance += 1
    #         other_tracer = other_tracer._parent
    #     return len(self_heritage)


class Species:

    """
    Data structure representing each species.

    Instance Attributes:
        - name_latin is the Latin for the species.
        - name_common is the common English name of the species.
        - vocal_data is the processed vocalization data of each species.

    Representation Invariants:
        - self.name_latin is not '' and self.name_common is not ''
    """

    name_latin: str
    name_common: str
    recording_data: RecordingData

    def __init__(self, name_latin: str, name_common: str, recording_datas: RecordingData) -> None:
        """Initialize the Species information."""
        self.name_latin = name_latin
        self.name_common = name_common
        self.recording_data = recording_datas


class RecordingData:
    """
    Data structure representing the analyzed recording data from averaging
    features of data obtained from Xeno-Canto.

    Instance Attributes:
        - self.recording_files: the recordings' directory
        - self.data: the recordings' analysis

    Representation Invariants:
        - self.recording_files =! []
        - all(feature in {'mfcc', 'pitch_mean', 'centroid_mean', 'bandwidth_mean', 'rms_mean'} for feature in features)
        - all data in self.features are extracted to a well-defined value

    """

    recording_paths: list[str]
    features: Optional[dict[str, Any]] = None

    def __init__(self, recording_files: list[str]):
        """
        Initialize the new RecordingData instance,
        with the file paths to analyse the features of the species' vocalization
        """
        self.recording_files = recording_files
        self.features = None
        self.average_features()

    def average_features(self) -> None:
        """Calculate the features of the recordings, and set the self.features to that corresponding value."""
        if not self.recording_files:
            self.features = {}
            return

        all_features = []
        for path in self.recording_files:
            feat = self._extract_feature(path)
            if feat is not None:
                all_features.append(feat)
        self.features = self._average_features(all_features)

    # def _average_features(self, features_list: list[dict[str, Any]]) -> dict[str, Any]:
    #     """Calculate the average of """
    #     if not features_list:
    #         return {}
    #     avg_features = {}
    #     keys = features_list[0].keys()
    #     for key in keys:
    #         values = []
    #         for f in features_list:
    #             if key in f:
    #                 values.append(f[key])
    #         if values != []:
    #             avg_features[key] = mean(values)
    #
    #     return avg_features

    def _average_features(self, features_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate the average of all features. Special handling for 'mfcc' which is a list."""
        if not features_list:
            return {}

        avg_features = {}
        keys = features_list[0].keys()

        for key in keys:
            if key == 'mfcc':
                num_mfcc = len(features_list[0]['mfcc'])   # 应该为 8
                mfcc_avg = []
                for i in range(num_mfcc):
                    values = [f['mfcc'][i] for f in features_list]
                    mfcc_avg.append(mean(values))
                avg_features['mfcc'] = mfcc_avg
            else:
                values = [f[key] for f in features_list if key in f]
                if values:
                    avg_features[key] = mean(values)

        return avg_features

    # def _extract_feature(self, file_path: str) -> Optional[dict[str, Any]]:
    #     """处理单条音频，增加预处理"""
    #     print(f"calculating{file_path}")
    #     # try:
    #     y, sr = librosa.load(file_path, sr=None)
    #
    #     # 1. 去除静音（非常重要！）
    #     y, _ = librosa.effects.trim(y, top_db=20)
    #
    #     # 2. 如果修剪后音频太短，跳过
    #     if len(y) < sr * 0.5:
    #         return None
    #
    #     # 3. 音量归一化（让不同录音的响度接近）
    #     y = librosa.util.normalize(y)
    #
    #     # 4. 提取特征
    #     mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    #
    #     f0, voiced_flag, _ = librosa.pyin(y,
    #                                       fmin=float(librosa.note_to_hz('C2')),
    #                                       fmax=float(librosa.note_to_hz('C7')),
    #                                       sr=sr)
    #     voiced_f0 = [float(f) for f, v in zip(f0, voiced_flag) if v and not math.isnan(f)]
    #
    #     cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    #     bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    #     rms = librosa.feature.rms(y=y)
    #
    #     return {
    #         'mfcc': [float(mean(mfcc[i])) for i in range(8)],
    #         'pitch_mean': mean(voiced_f0) if voiced_f0 else 0.0,
    #         'centroid_mean': float(mean(cent[0])),
    #         'bandwidth_mean': float(mean(bw[0])),
    #         'rms_mean': float(mean(rms[0]))
    #     }
    #
    #     # except Exception as e:
    #     #     print(f"提取特征失败 {file_path}: {e}")
    #     #     return None

    def _extract_feature(self, file_path: str) -> Optional[dict[str, Any]]:
        """处理单条音频，增加强预处理"""
        print(f"calculating{file_path}")
        # try:
        y, sr = librosa.load(file_path, sr=None)

        # 1. 强力去除静音
        y, _ = librosa.effects.trim(y, top_db=30)  # 从20改成30，更激进

        # 2. 如果音频还是太短，跳过
        if len(y) < sr * 0.8:  # 从0.5秒提高到0.8秒
            return None

        # 3. 高通滤波（去除低频噪声，非常重要！）
        y = librosa.effects.preemphasis(y, coef=0.97)

        # 4. 音量归一化
        y = librosa.util.normalize(y)

        # 5. 提取特征
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, fmin=100)  # 加上 fmin=100

        f0, voiced_flag, _ = librosa.pyin(y,
                                          fmin=float(librosa.note_to_hz('C2')),
                                          fmax=float(librosa.note_to_hz('C7')),
                                          sr=sr)

        voiced_f0 = [float(f) for f, v in zip(f0, voiced_flag) if v and not math.isnan(f)]

        cent = librosa.feature.spectral_centroid(y=y, sr=sr)
        bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)

        return {
            'mfcc': [float(mean(mfcc[i])) for i in range(8)],
            'pitch_mean': mean(voiced_f0) if voiced_f0 else 0.0,
            'centroid_mean': float(mean(cent[0])),
            'bandwidth_mean': float(mean(bw[0])),
            'rms_mean': float(mean(rms[0]))
        }

        # except Exception as e:
        #     print(f"提取特征失败 {file_path}: {e}")
        #     return None


    # def _extract_feature(self, file_path: str) -> Optional[dict[str, Any]]:
    #     """Private method to analyse the features of a single recording file."""
    #     print(f"calculating{file_path}")
    #     y, sr = librosa.load(file_path, sr=None)
    #
    #     if len(y) < sr * 0.5:
    #         return None
    #
    #     mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    #     f0, voiced_flag, _ = librosa.pyin(y,
    #                                       fmin=float(librosa.note_to_hz('C2')),
    #                                       fmax=float(librosa.note_to_hz('C7')),
    #                                       sr=sr)
    #     voiced_f0 = [float(f) for f, v in zip(f0, voiced_flag) if v and not math.isnan(f)]
    #     cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    #     bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    #     rms = librosa.feature.rms(y=y)
    #     return {
    #         'mfcc': [float(mean(mfcc[i])) for i in range(8)],
    #         'pitch_mean': mean(voiced_f0) if voiced_f0 else 0.0,
    #         'centroid_mean': float(mean(cent[0])),
    #         'bandwidth_mean': float(mean(bw[0])),
    #         'rms_mean': float(mean(rms[0]))
    #     }

    def get_feature_vector(self) -> list[float]:
        """Return the one-dimensional array of the features of the data, which is later used for calculating distance.
        """
        if not self.features:
            return []

        vector = self.features.get('mfcc', [])[:]
        for key in ['pitch_mean', 'centroid_mean', 'bandwidth_mean', 'rms_mean']:
            vector.append(self.features.get(key, 0.0))
        return vector




#     def __init__(self, recording_file: str) -> None:
#         """Initialize a set of analyzed data from the list of recording files."""
#         self.recording_file = recording_file
#         # self.extract_data()
#         # data = self.extract_data()
#     #     self.某data = data.[某data]
#
#     def extract_data(self) -> None:
#         """Analyse the recording file and compute the mean data for the species."""
# #         TODO: complete the function


# variables for testing
# Parus_major = TaxonomyTree(
#     rank='Species',
#     root='Parus_major',
#     subtrees=None,
#     parent=None,
#     species=Species('Parus_major', 'Great_Tit', RecordingData(['']))
# )
# Parus_minor = TaxonomyTree(
#     rank='Species',
#     root='Parus_minor',
#     subtrees=None,
#     parent=None,
#     species=Species('Parus_minor', 'Japanese_tit', RecordingData(['']))
# )
# tree = TaxonomyTree(
#     rank='Class',
#     root='Aves',
#     subtrees=[TaxonomyTree(
#         rank='Order',
#         root='Passeriformes',
#         subtrees=[TaxonomyTree(
#             rank='Family',
#             root='Paridae',
#             subtrees=[TaxonomyTree(
#                 rank='Genus',
#                 root='Parus',
#                 subtrees=[Parus_major, Parus_minor])])])]
# )
