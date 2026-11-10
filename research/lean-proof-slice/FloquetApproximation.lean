import Mathlib

namespace Sylva.RoomTempSuperconductivity

open Real

/-- Explicit absolute-error bound; no equivalence type class is introduced. -/
def DriveApprox (ω_drive Δ ℏ ε : ℝ) : Prop :=
  |ω_drive - 2 * Δ / ℏ| ≤ ε

/-- Definitional unfolding only; this is not a Floquet enhancement proof. -/
theorem driveApprox_unfold (ω_drive Δ ℏ ε : ℝ) :
    DriveApprox ω_drive Δ ℏ ε = (|ω_drive - 2 * Δ / ℏ| ≤ ε) := by
  rfl

/-- Zero error recovers the exact drive relation. -/
theorem driveApprox_zero_exact (ω_drive Δ ℏ : ℝ)
    (h : DriveApprox ω_drive Δ ℏ 0) :
    ω_drive = 2 * Δ / ℏ := by
  have h_abs : |ω_drive - 2 * Δ / ℏ| = 0 :=
    le_antisymm h (abs_nonneg _)
  exact sub_eq_zero.mp (abs_eq_zero.mp h_abs)

/-- Exact equality gives the zero-error bound. -/
theorem driveApprox_of_exact (ω_drive Δ ℏ : ℝ)
    (h : ω_drive = 2 * Δ / ℏ) :
    DriveApprox ω_drive Δ ℏ 0 := by
  simp [h, DriveApprox]

#print axioms driveApprox_unfold
#print axioms driveApprox_zero_exact
#print axioms driveApprox_of_exact

end Sylva.RoomTempSuperconductivity
