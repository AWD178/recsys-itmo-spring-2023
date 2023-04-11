from .random import Random
from .recommender import Recommender
import random


class ContextualWithMemory(Recommender):
    """
    Recommend tracks closest to the best from several previous one.
    Best == the one, which was listened the longest.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, catalog, history_tracker, n_tracks_to_keep):
        self.tracks_redis = tracks_redis
        self.fallback = Random(tracks_redis)
        self.catalog = catalog
        self.history_tracker = history_tracker
        self.n_tracks_to_keep = n_tracks_to_keep

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        if user not in self.history_tracker:
            self.history_tracker[user] = [(prev_track, prev_track_time)]
        else:
            self.history_tracker[user].append((prev_track, prev_track_time))

            if len(self.history_tracker[user]) > self.n_tracks_to_keep:
                self.history_tracker[user] = self.history_tracker[user][-self.n_tracks_to_keep:]


        best_prev_track = max(self.history_tracker[user], key=lambda track_and_time: track_and_time[1])[0]
        best_previous_track = self.tracks_redis.get(best_prev_track)

        best_previous_track = self.catalog.from_bytes(best_previous_track)
        recommendations = best_previous_track.recommendations
        if not recommendations:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        shuffled = list(recommendations)
        random.shuffle(shuffled)
        return shuffled[0]

