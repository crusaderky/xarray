from __future__ import annotations

import importlib
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, Final, Protocol, TypeVar

import numpy as np

if TYPE_CHECKING:
    if sys.version_info >= (3, 10):
        from typing import TypeGuard
    else:
        from typing_extensions import TypeGuard

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    try:
        from dask.array import Array as DaskArray
        from dask.types import DaskCollection
    except ImportError:
        DaskArray = np.ndarray  # type: ignore
        DaskCollection: Any = np.ndarray  # type: ignore


# https://stackoverflow.com/questions/74633074/how-to-type-hint-a-generic-numpy-array
T_DType_co = TypeVar("T_DType_co", bound=np.dtype[np.generic], covariant=True)
# T_DType = TypeVar("T_DType", bound=np.dtype[np.generic])


class _Array(Protocol[T_DType_co]):
    @property
    def dtype(self) -> T_DType_co:
        ...

    @property
    def shape(self) -> tuple[int, ...]:
        ...

    @property
    def real(self) -> Self:
        ...

    @property
    def imag(self) -> Self:
        ...

    def astype(self, dtype: np.typing.DTypeLike) -> Self:
        ...

    # TODO: numpy doesn't use any inputs:
    # https://github.com/numpy/numpy/blob/v1.24.3/numpy/_typing/_array_like.py#L38
    def __array__(self) -> np.ndarray[Any, T_DType_co]:
        ...


class _ChunkedArray(_Array[T_DType_co], Protocol[T_DType_co]):
    @property
    def chunks(self) -> tuple[tuple[int, ...], ...]:
        ...


# temporary placeholder for indicating an array api compliant type.
# hopefully in the future we can narrow this down more
T_DuckArray = TypeVar("T_DuckArray", bound=_Array[np.dtype[np.generic]])
T_ChunkedArray = TypeVar("T_ChunkedArray", bound=_ChunkedArray[np.dtype[np.generic]])


# Singleton type, as per https://github.com/python/typing/pull/240
class Default(Enum):
    token: Final = 0


_default = Default.token


def module_available(module: str) -> bool:
    """Checks whether a module is installed without importing it.

    Use this for a lightweight check and lazy imports.

    Parameters
    ----------
    module : str
        Name of the module.

    Returns
    -------
    available : bool
        Whether the module is installed.
    """
    return importlib.util.find_spec(module) is not None


def is_dask_collection(x: object) -> TypeGuard[DaskCollection]:
    if module_available("dask"):
        from dask.typing import DaskCollection

        return isinstance(x, DaskCollection)
    return False


def is_duck_array(value: object) -> TypeGuard[T_DuckArray]:
    if isinstance(value, np.ndarray):
        return True
    return (
        hasattr(value, "ndim")
        and hasattr(value, "shape")
        and hasattr(value, "dtype")
        and (
            (hasattr(value, "__array_function__") and hasattr(value, "__array_ufunc__"))
            or hasattr(value, "__array_namespace__")
        )
    )


def is_duck_dask_array(x: T_DuckArray) -> TypeGuard[DaskArray]:
    return is_dask_collection(x)


def is_chunked_duck_array(
    x: T_DuckArray,
) -> TypeGuard[_ChunkedArray[np.dtype[np.generic]]]:
    return hasattr(x, "chunks")


def to_0d_object_array(
    value: object,
) -> np.ndarray[Any, np.dtype[np.object_]]:
    """Given a value, wrap it in a 0-D numpy.ndarray with dtype=object."""
    result = np.empty((), dtype=object)
    result[()] = value
    return result