import os
import unittest
from util import BurnManTest
import numpy as np
from numpy import random
import matplotlib.pyplot as plt

import burnman
from burnman.optimize.eos_fitting import fit_XPTp_data
from burnman.optimize.nonlinear_fitting import nonlinear_least_squares_fit
from burnman.utils.misc import attribute_function, pretty_string_values

path = os.path.dirname(os.path.abspath(__file__))


class test_fitting(BurnManTest):
    def test_linear_fit(self):
        # Test from Neri et al. (Meas. Sci. Technol. 1 (1990) 1007-1010.)
        i, x, Wx, y, Wy = np.loadtxt(
            f"{path}/../burnman/data/" "input_fitting/Pearson_York.dat", unpack=True
        )

        data = np.array([x, y]).T
        cov = np.array([[1.0 / Wx, 0.0 * Wx], [0.0 * Wy, 1.0 / Wy]]).T

        class m:
            def __init__(self, data, cov, guessed_params, delta_params):
                self.data = data
                self.data_covariances = cov
                self.set_params(guessed_params)
                self.delta_params = delta_params
                # irrelevant for a linear model
                self.mle_tolerances = np.array([1.0e-1] * len(data[:, 0]))

            def set_params(self, param_values):
                self.params = param_values

            def get_params(self):
                return self.params

            def function(self, x, flag):
                return np.array([x[0], self.params[0] * x[0] + self.params[1]])

            def normal(self, x, flag):
                n = np.array([self.params[0], -1.0])
                return n / np.linalg.norm(n)

        guessed_params = np.array([-0.5, 5.5])
        # unimportant for a linear model
        delta_params = np.array([1.0e-3, 1.0e-3])
        fitted_curve = m(data, cov, guessed_params, delta_params)
        nonlinear_least_squares_fit(model=fitted_curve, param_tolerance=1.0e-5)

        self.assertArraysAlmostEqual([fitted_curve.WSS], [11.8663531941])

    def test_polynomial_fit(self):
        # Test from Neri et al. (Meas. Sci. Technol. 1 (1990) 1007-1010.)
        i, x, Wx, y, Wy = np.loadtxt(
            f"{path}/../burnman/data/" "input_fitting/Pearson_York.dat", unpack=True
        )

        data = np.array([x, y]).T
        cov = np.array([[1.0 / Wx, 0.0 * Wx], [0.0 * Wy, 1.0 / Wy]]).T

        class m:
            def __init__(self, data, cov, guessed_params, delta_params):
                self.data = data
                self.data_covariances = cov
                self.set_params(guessed_params)
                self.delta_params = delta_params
                self.mle_tolerances = np.array([1.0e-8] * len(data[:, 0]))

            def set_params(self, param_values):
                self.params = param_values

            def get_params(self):
                return self.params

            def function(self, x, flag):
                return np.array(
                    [
                        x[0],
                        self.params[0] * x[0] * x[0] * x[0]
                        + self.params[1] * x[0] * x[0]
                        + self.params[2] * x[0]
                        + self.params[3],
                    ]
                )

            def normal(self, x, flag):
                n = np.array(
                    [
                        3.0 * self.params[0] * x[0] * x[0]
                        + 2.0 * self.params[1] * x[0]
                        + 1.0 * self.params[2],
                        -1.0,
                    ]
                )
                return n / np.linalg.norm(n)

        guessed_params = np.array([-1.2e-2, 0.161, -1.15, 6.142])
        delta_params = np.array([1.0e-5, 1.0e-5, 1.0e-5, 1.0e-5])
        fitted_curve = m(data, cov, guessed_params, delta_params)
        nonlinear_least_squares_fit(model=fitted_curve, param_tolerance=1.0e-5)
        self.assertArraysAlmostEqual([fitted_curve.WSS], [10.486904577])

    def test_fit_PVT_data(self):
        fo = burnman.minerals.HP_2011_ds62.fo()

        pressures = np.linspace(1.0e9, 2.0e9, 8)
        temperatures = np.ones_like(pressures) * fo.params["T_0"]

        PTV = np.empty((len(pressures), 3))

        for i in range(len(pressures)):
            fo.set_state(pressures[i], temperatures[i])
            PTV[i] = [pressures[i], temperatures[i], fo.V]

        params = ["V_0", "K_0", "Kprime_0"]
        fitted_eos = burnman.eos_fitting.fit_PTV_data(fo, params, PTV, verbose=False)
        zeros = np.zeros_like(fitted_eos.pcov[0])

        self.assertArraysAlmostEqual(fitted_eos.pcov[0], zeros)

    def test_fit_bounded_PVT_data(self):
        fo = burnman.minerals.HP_2011_ds62.fo()

        pressures = np.linspace(0.0e9, 10.0e9, 8)
        temperatures = np.ones_like(pressures) * fo.params["T_0"]

        PTV = np.empty((len(pressures), 3))

        for i in range(len(pressures)):
            fo.set_state(pressures[i], temperatures[i])
            PTV[i] = [pressures[i], temperatures[i], fo.V]

        # Modify the lowest and highest pressure points
        # to artificially reduce the value of K'0
        PTV[0, 2] *= 1.01
        PTV[-1, 2] *= 0.99

        params = ["V_0", "K_0", "Kprime_0"]
        bounds = np.array([[0.0, np.inf], [0.0, np.inf], [3.0, 4.0]])
        fitted_eos = burnman.eos_fitting.fit_PTV_data(
            fo, params, PTV, bounds=bounds, verbose=False
        )

        cp_bands = burnman.nonlinear_fitting.confidence_prediction_bands(
            model=fitted_eos,
            x_array=PTV,
            confidence_interval=0.95,
            f=attribute_function(fo, "V"),
            flag="V",
        )
        self.assertEqual(len(cp_bands[0]), len(PTV))
        self.assertEqual(len(cp_bands), 4)

        self.assertFloatEqual(3.0, fitted_eos.popt[2])

        s = pretty_string_values(
            fitted_eos.popt,
            fitted_eos.pcov,
            extra_decimal_places=1,
            combine_value_and_sigma=False,
        )

        self.assertEqual(len(s), 3)
        self.assertEqual(len(s[0]), 3)
        self.assertEqual(len(s[1]), 3)
        self.assertEqual(len(s[2]), 3)

        s = pretty_string_values(
            fitted_eos.popt,
            fitted_eos.pcov,
            extra_decimal_places=1,
            combine_value_and_sigma=True,
        )

        self.assertEqual(len(s), 3)
        self.assertEqual(len(s[0]), 3)
        self.assertEqual(len(s[1]), 3)
        self.assertEqual(len(s[2]), 3)

    def test_bounded_solution_fitting(self):
        solution = burnman.minerals.SLB_2011.mg_fe_olivine()
        solution.set_state(1.0e5, 300.0)
        fit_params = [["V_0", 0], ["V_0", 1], ["V", 0, 1]]

        n_data = 5
        data = []
        data_covariances = []
        flags = []

        f_Verror = 1.0e-3

        # Choose a specific seed so that the test is reproducible.
        random.seed(10)
        for i in range(n_data):
            x_fa = random.random()
            P = random.random() * 1.0e10
            T = random.random() * 1000.0 + 300.0
            X = [1.0 - x_fa, x_fa]
            solution.set_composition(X)
            solution.set_state(P, T)
            f = 1.0 + (random.normal() - 0.5) * f_Verror
            V = solution.V * f

            data.append([1.0 - x_fa, x_fa, P, T, V])
            data_covariances.append(np.zeros((5, 5)))
            data_covariances[-1][4, 4] = np.power(solution.V * f_Verror, 2.0)

        flags = ["V"] * 5

        n_data = 2
        f_Vperror = 1.0e-2

        for i in range(n_data):
            x_fa = random.random()
            P = random.random() * 1.0e10
            T = random.random() * 1000.0 + 300.0
            X = [1.0 - x_fa, x_fa]
            solution.set_composition(X)
            solution.set_state(P, T)
            f = 1.0 + (random.normal() - 0.5) * f_Vperror
            Vp = solution.p_wave_velocity * f

            data.append([1.0 - x_fa, x_fa, P, T, Vp])
            data_covariances.append(np.zeros((5, 5)))
            data_covariances[-1][4, 4] = np.power(
                solution.p_wave_velocity * f_Vperror, 2.0
            )
            flags.append("p_wave_velocity")

        data = np.array(data)
        data_covariances = np.array(data_covariances)
        flags = np.array(flags)
        delta_params = np.array([1.0e-8, 1.0e-8, 1.0e-8])
        bounds = np.array([[0, np.inf], [0, np.inf], [-np.inf, np.inf]])

        fitted_eos = fit_XPTp_data(
            solution=solution,
            flags=flags,
            fit_params=fit_params,
            data=data,
            data_covariances=data_covariances,
            delta_params=delta_params,
            bounds=bounds,
            param_tolerance=1.0e-5,
            verbose=False,
        )

        self.assertEqual(len(fitted_eos.popt), 3)

        cp_bands = burnman.nonlinear_fitting.confidence_prediction_bands(
            model=fitted_eos,
            x_array=data,
            confidence_interval=0.95,
            f=attribute_function(solution, "V"),
            flag="V",
        )
        self.assertEqual(len(cp_bands[0]), len(data))
        self.assertEqual(len(cp_bands), 4)

        good_data_confidence_interval = 0.9
        _, indices, probabilities = burnman.nonlinear_fitting.extreme_values(
            fitted_eos.weighted_residuals, good_data_confidence_interval
        )
        self.assertEqual(len(indices), 0)
        self.assertEqual(len(probabilities), 0)

        # Just check plotting doesn't return an error
        fig, ax = plt.subplots()
        burnman.nonlinear_fitting.plot_residuals(
            ax=ax,
            weighted_residuals=fitted_eos.weighted_residuals,
            flags=fitted_eos.flags,
        )
        fig, ax = plt.subplots()
        burnman.nonlinear_fitting.weighted_residual_plot(ax, fitted_eos)

        fig, ax = burnman.nonlinear_fitting.corner_plot(
            fitted_eos.popt, fitted_eos.pcov
        )


if __name__ == "__main__":
    unittest.main()
