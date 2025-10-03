import numpy as np
import matplotlib.pyplot as plt

def random_walks(n: int, T: int, p: float, seed: int | None = None):
    """
    Simule n marches aléatoires 1D de longueur T avec proba p de +1 (sinon -1).

    Paramètres
    ----------
    n : nombre de marches
    T : nombre de pas par marche
    p : probabilité d'un pas +1 (entre 0 et 1)
    seed : graine aléatoire (optionnelle)

    Retour
    ------
    positions : np.ndarray de shape (n, T+1)
        positions cumulées à partir de 0 (colonne 0 = 0)
    """
    if not (0 <= p <= 1):
        raise ValueError("p doit être dans [0, 1].")
    if n <= 0 or T <= 0:
        raise ValueError("n et T doivent être des entiers positifs.")

    rng = np.random.default_rng(seed)
    # Tirages: +1 avec proba p, sinon -1
    steps = np.where(rng.random((n, T)) < p, 1, -1)
    # Positions cumulées, en partant de 0
    positions = np.cumsum(steps, axis=1)
    positions = np.concatenate([np.zeros((n, 1), dtype=int), positions], axis=1)
    return positions

def plot_walks(positions: np.ndarray, show_mean: bool = True, alpha: float = 0.8):
    """
    Trace les marches aléatoires fournies (shape (n, T+1)).
    """
    n, Tp1 = positions.shape
    T = Tp1 - 1

    plt.figure(figsize=(10, 6))
    for i in range(n):
        # éviter une légende surchargée : on n’ajoute qu’une entrée si n <= 10
        label = f"Marche {i+1}" if n <= 10 else None
        plt.plot(range(T+1), positions[i], linewidth=1.2, alpha=alpha, label=label)

    if show_mean:
        mean_traj = positions.mean(axis=0)
        plt.plot(range(T+1), mean_traj, linewidth=2.5, label="Moyenne", zorder=10)

    plt.title(f"{n} marches aléatoires (T={T}) – pas +1 avec p")
    plt.xlabel("Pas")
    plt.ylabel("Position")
    if n <= 10 or show_mean:
        plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Exemple d'utilisation
    n = 100      # nombre de marches
    T = 10000     # nombre de pas par marche
    p = 0.495    # probabilité d'un pas +1
    seed = 42   # pour reproductibilité (optionnel)

    positions = random_walks(n, T, p, seed=seed)
    plot_walks(positions, show_mean=True)

