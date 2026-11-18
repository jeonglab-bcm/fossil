"""Small helpers shared by the pipeline steps."""
import io
import zipfile

import numpy as np


def save_npz(path, **arrays):
    """np.savez_compressed with a fixed timestamp on every member, so a rerun writes the same bytes."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(arrays):
            buf = io.BytesIO()
            np.lib.format.write_array(buf, np.asanyarray(arrays[name]), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, buf.getvalue())
