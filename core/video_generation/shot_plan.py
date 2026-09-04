from dataclasses import dataclass, field
from typing import List


@dataclass
class Shot:
    duration: float
    visual: str

    # حركة الكاميرا
    camera: str = "static"

    # انتقالات
    transition_in: str = "cut"
    transition_out: str = "cut"

    # عناصر إضافية
    text: str = ""
    sound_effect: str = ""
    music: str = ""

    # مؤثرات بصرية
    effects: List[str] = field(default_factory=list)


@dataclass
class VideoSequence:
    title: str
    shots: List[Shot]

    @property
    def duration(self):
        return sum(shot.duration for shot in self.shots)


def example_cinematic_sequence():
    return VideoSequence(
        title="مثال سينمائي",
        shots=[
            Shot(
                duration=4,
                visual="سماء ليلية مليئة بالنجوم",
                camera="slow_zoom_in",
                transition_in="fade",
                effects=["film_grain", "vignette"],
            ),

            Shot(
                duration=3,
                visual="مقص معدني يدور في الهواء بإضاءة سينمائية",
                camera="orbit",
                transition_in="cut",
                effects=["motion_blur", "slow_motion"],
                sound_effect="whoosh",
            ),

            Shot(
                duration=5,
                visual="أستاذ يقف أمام خلفية حديثة ويشرح",
                camera="push_in",
                transition_in="cut",
                text="الفكرة الأساسية",
            ),

            Shot(
                duration=3,
                visual="لقطة قريبة جداً للمقص أثناء إغلاقه",
                camera="macro_push",
                transition_in="match_cut",
                effects=["motion_blur"],
                sound_effect="metal_click",
            ),

            Shot(
                duration=4,
                visual="لقطة واسعة للمشهد بالكامل",
                camera="pull_back",
                transition_in="crossfade",
            ),
        ],
    )
