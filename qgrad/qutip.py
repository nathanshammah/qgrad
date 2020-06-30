"""
Implementation of some common quantum mechanics functions that work with Jax
"""
from scipy.sparse import csr_matrix
from jax.ops import index, index_update
import jax.numpy as jnp
from scipy.linalg import expm, sqrtm
from numpy.linalg import matrix_power

def fidelity(a, b):
    """
    Computes fidelity between two states (pure or mixed).
    
    Args:
        a (`:obj:numpy.ndarray`): State vector (ket) or a density
             matrix. Pure Python list can also be passed for a ket.
        b (`:obj:numpy.ndarray`): State vector (ket) or a density
             matrix. Pure Python list can also be passed for a ket.
        
    Returns:
        float: fidelity between the two states
    """
    if jnp.asarray(a).shape[1] >= 2 or jnp.asarray(b).shape[1] >= 2:
        return _fidelity_dm(a, b)

    else:
        return _fidelity_ket(a, b)


# TODO: Add tests with python list inputs for fidel and expect
def _fidelity_ket(a, b):
    """
    Private function that computes fidelity between two kets.
    
    Args:
        a (`:obj:numpy.ndarray`): State vector (ket) or a Python list
        b (`:obj:numpy.ndarray`): State vector (ket) or a Python list
        
    Returns:
        float: fidelity between the two state vectors
    """
    a, b = jnp.asarray(a), jnp.asarray(b)
    return jnp.abs(jnp.dot(jnp.transpose(jnp.conjugate(a)), b)) ** 2


def _fidelity_dm(a, b):
    """
    Private function that computes fidelity among two mixed states.
    
    Args:
        a (`:obj:numpy.ndarray`): density matrix (density matrix)
        b (`:obj:numpy.ndarray`): density matrix (density matrix)
        
    Returns:
        float: fidelity between the two density matrices 
    """
    dm1, dm2 = jnp.asarray(a), jnp.asarray(b)
    return jnp.trace(sqrtm(jnp.dot(jnp.dot(sqrtm(dm1), dm2), sqrtm(dm1)))) ** 2


def rot(params):
    """
    Returns a unitary matrix describing rotation around Z-Y-Z axis

    Args:
        params (`:obj:numpy.array`[float]): an array of three parameters defining the
                                     rotation

    Returns:
        `:obj:numpy.array`[complex]: a 2x2 matrix defining the unitary
    """
    phi, theta, omega = params
    cos = jnp.cos(theta / 2)
    sin = jnp.sin(theta / 2)

    return jnp.array(
        [
            [
                jnp.exp(-0.5j * (phi + omega)) * cos,
                -(jnp.exp(0.5j * (phi - omega))) * sin,
            ],
            [jnp.exp(-0.5j * (phi - omega)) * sin, jnp.exp(0.5j * (phi + omega)) * cos],
        ]
    )


def sigmax():
    r"""Returns a Pauli-X operator
    .. math:: \sigma_{x} = \begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}. 
    
    Examples
    -------
    >>>sigmax()
    [[0. 1.]
     [1. 0.]]

    """
    return jnp.asarray([[0.0, 1.0], [1.0, 0.0]])


def sigmay():
    r"""Returns a Pauli-Y operator
    .. math:: \sigma_{y} = \begin{bmatrix} 0 & -i \\ i & 0 \end{bmatrix}. 
    
    Examples
    -------
    >>>sigmay()
    [[0.+0.j 0.-1.j]
     [0.+1.j 0.+0.j]]

    """
    return jnp.asarray([[0.0 + 0.0j, 0.0 - 1.0j], [0.0 + 1.0j, 0.0 + 0.0j]])


def sigmaz():
    r"""Returns a Pauli-Y operator
    .. math:: \sigma_{z} = \begin{bmatrix} 1 & 0 \\ 0 & -1 \end{bmatrix}. 
    
    Examples
    -------
    >>>sigmaz()
    [[1. 0.]
     [0. -1.]]

    """
    return jnp.asarray([[1.0, 0.0], [0.0, -1.0]])


def destroy(N, full=False):
    """Destruction (lowering or annihilation) operator.
    
    Args:
        N (int): Dimension of Hilbert space.
        full (bool): Returns a full matrix if `True` and Compressed Sparse Matrix if `False`  

    Returns:
         `obj:numpy.array`[complex]: Matrix representation for an N-dimensional annihilation operator

    """
    if not isinstance(N, (int, jnp.integer)):  # raise error if N not integer
        raise ValueError("Hilbert space dimension must be an integer value")
    data = jnp.sqrt(jnp.arange(1, N, dtype=jnp.float32))
    ind = jnp.arange(1, N, dtype=jnp.float32)
    ptr = jnp.arange(N + 1, dtype=jnp.float32)
    index_update(
        ptr, index[-1], N - 1
    )  # index_update mutates the jnp array in-place like numpy
    return (
        csr_matrix((data, ind, ptr), shape=(N, N))
        if full is True
        else csr_matrix((data, ind, ptr), shape=(N, N)).toarray()
    )


# TODO: Add test destroy(N).dag() == create(N)
def create(N, full=False):
    """Creation (raising) operator.

    Args:
        N (int): Dimension of Hilbert space 
        full (bool): Returns a full matrix if `True` and Compressed Sparse Matrix if `False`  

    Returns:
         `obj:numpy.array`[complex]: Matrix representation for an N-dimensional creation operator

    """

    if not isinstance(N, (int, jnp.integer)):  # raise error if N not integer
        raise ValueError("Hilbert space dimension must be an integer value")
    data = jnp.sqrt(jnp.arange(1, N, dtype=jnp.float32))
    ind = jnp.arange(0, N - 1, dtype=jnp.float32)
    ptr = jnp.arange(N + 1, dtype=jnp.float32)
    index_update(
        ptr, index[0], 0
    )  # index_update mutates the jnp array in-place like numpy
    return (
        csr_matrix((data, ind, ptr), shape=(N, N))
        if full is True
        else csr_matrix((data, ind, ptr), shape=(N, N)).toarray()
    )


def expect(oper, state):
    """Calculates the expectation value of an operator 
    with respect to a given (pure or mixed) state.

    Args:
        oper (`:obj:numpy.ndarray`): Numpy array representing
                an operator
        state (`:obj:numpy.ndarray`): Numpy array representing 
                a density matrix. Standard Python list can also be                 passed in case of a pure state (ket).

    Returns:
        expt (float): Expectation value. ``real`` if the `oper` is
                Hermitian and ``complex`` otherwise 
    """
    if jnp.asarray(state).shape[1] >= 2:
        return _expect_dm(oper, state)

    else:
        return _expect_ket(oper, state)


def _expect_dm(oper, state):
    """Private function to calculate the expectaion value of 
    and operator with respect to a density matrix
    """
    # convert to jax.numpy arrays in case user gives raw numpy
    oper, rho = jnp.asarray(oper), jnp.asarray(state)
    # Tr(rho*op)
    return jnp.trace(jnp.dot(rho, oper))


def _expect_ket(oper, state):
    """Private function to calculate the expectaion value of 
    and operator with respect to a ket
    """
    oper, ket = jnp.asarray(oper), jnp.asarray(state)
    return jnp.vdot(jnp.transpose(ket), jnp.dot(oper, ket))

class Displacer:
    r"""Displacement operator for optical phase space
    
    .. math: D(\alpha) = \exp(\alpha a^\dagger -\alpha^* a)

    Args:
    ----
    n (int): dimension of the displace operator
    """
    def __init__(self, n):
        # The off-diagonal of the real-symmetric similar matrix T.
        sym = (2*(np.arange(1, n)%2) - 1) * np.sqrt(np.arange(1, n))
        # Solve the eigensystem.
        self.evals, self.evecs = scipy.linalg.eigh_tridiagonal(np.zeros(n), sym)
        self.range = np.arange(n)
        self.t_scale = 1j**(self.range % 2)

    def __call__(self, alpha):
        """Callable with alpha as the displacement parameter"""
        # Diagonal of the transformation matrix P, and apply to eigenvectors.
        transform = self.t_scale * (alpha / np.abs(alpha))**-self.range
        evecs = transform[:, None] * self.evecs
        # Get the exponentiated diagonal.
        diag = np.exp(1j * np.abs(alpha) * self.evals)
        return np.conj(evecs) @ (diag[:, None] * evecs.T)

def squeeze(N, z):
    """Single-mode squeezing operator

    Args:
    ----
    N (int): Dimension of Hilbert space

    z (float/complex): Squeezing parameter

    Returns:
    ------- 
    `obj:numpy.array`[complex]: Squeezing operator
    
    """
    op = (1.0 / 2.0) * ((jnp.conj(z) * matrix_power(destroy(N), 2)) - (z * matrix_power(create(N), 2)))
    return expm(op)


