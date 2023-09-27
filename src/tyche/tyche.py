import json
import pprint
import coverage

global features
features = {}


def features_for_value(value, feature_type):
    dicts = [(fname, f) for ty, feats in features.items() for fname, f in feats.items()
             if isinstance(value, ty) and type(f(value)) == feature_type]
    return dict(dicts)


def setup():
    cov = coverage.Coverage(omit=["tyche.py", "**/hypothesis/*", "**/python/*"])
    cov.start()
    return cov


def analyze(f, cov):
    old_inner = f.hypothesis.inner_test
    ls = []

    def new_inner(*args, **kwargs):
        ls.append(kwargs)
        old_inner(*args, **kwargs)

    f.hypothesis.inner_test = new_inner

    f()
    cov.stop()

    cov_report = []
    for file in cov.get_data().measured_files():
        (_, executable, missing, _) = cov.analysis(file)
        if len(executable) == 0:
            continue
        cov_report.append((file, {
            "percentage": (len(executable) - len(missing)) / len(executable),
            "hitLines": [i for i in executable if i not in missing],
            "missedLines": missing,
        }))

    return json.dumps({
        "coverage":
        dict(cov_report),
        "samples": [{
            "item":
            pprint.pformat(list(l.values())[0], width=50, compact=True)
            if len(l) == 1 else pprint.pformat(l, width=50, compact=True),
            "features":
            dict([(f"{k}_{feature}", f(v)) for k, v in l.items()
                  for feature, f in features_for_value(v, int).items()]),
            "bucketings":
            dict([(f"{k}_{bucketing}", f(v)) for k, v in l.items()
                  for bucketing, f in features_for_value(v, str).items()] +
                 [(f"{k}_{bucketing}", str(f(v))) for k, v in l.items()
                  for bucketing, f in features_for_value(v, bool).items()]),
        } for l in ls]
    })


def visualize(f, cov):
    print(analyze(f, cov))
