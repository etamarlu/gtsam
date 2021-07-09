"""
GTSAM Copyright 2010-2019, Georgia Tech Research Corporation,
Atlanta, Georgia 30332-0415
All Rights Reserved

See LICENSE for the license information

Cal3Unified unit tests.
Author: Frank Dellaert & Duy Nguyen Ta (Python)
"""
import unittest

import numpy as np

import gtsam
from gtsam.utils.test_case import GtsamTestCase
from gtsam.symbol_shorthand import K, L, P


class TestCal3Unified(GtsamTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Stereographic fisheye projection
        
        An equidistant fisheye projection with focal length f is defined
        as the relation r/f = 2*tan(theta/2), with r being the radius in the 
        image plane and theta the incident angle of the object point.
        """
        x, y, z = 1.0, 0.0, 1.0
        r = np.linalg.norm([x, y, z])
        u, v = 2*x/(z+r), 0.0
        #u, v = 2*np.tan(np.arctan2(x, z)/2), 0.0
        cls.obj_point = np.array([x, y, z])
        cls.img_point = np.array([u, v])

        fx, fy, s, u0, v0 = 2, 2, 0, 0, 0
        k1, k2, p1, p2 = 0, 0, 0, 0
        xi = 1
        cls.stereographic = gtsam.Cal3Unified(fx, fy, s, u0, v0, k1, k2, p1, p2, xi)

    def test_Cal3Unified(self):
        K = gtsam.Cal3Unified()
        self.assertEqual(K.fx(), 1.)
        self.assertEqual(K.fx(), 1.)

    def test_distortion(self):
        """Stereographic fisheye model of focal length f, defined as r/f = 2*tan(theta/2)"""
        x, y, z = self.obj_point
        r = np.linalg.norm([x, y, z])
        # Note: 2*tan(atan2(x, z)/2) = 2*x/(z+sqrt(x^2+z^2))
        self.assertAlmostEqual(2*np.tan(np.arctan2(x, z)/2), 2*x/(z+r))
        perspective_pt = self.obj_point[0:2]/self.obj_point[2]
        distorted_pt = self.stereographic.uncalibrate(perspective_pt)
        rectified_pt = self.stereographic.calibrate(distorted_pt)
        self.gtsamAssertEquals(distorted_pt, self.img_point)
        self.gtsamAssertEquals(rectified_pt, perspective_pt)

    def test_pinhole(self):
        """Spatial stereographic camera projection"""
        x, y, z = self.obj_point
        u, v = self.img_point
        r = np.linalg.norm(self.obj_point)
        pose = gtsam.Pose3()
        camera = gtsam.PinholeCameraCal3Unified(pose, self.stereographic)
        pt1 = camera.Project(self.obj_point)
        self.gtsamAssertEquals(pt1, np.array([x/z, y/z]))
        pt2 = camera.project(self.obj_point)
        self.gtsamAssertEquals(pt2, self.img_point)
        obj1 = camera.backproject(self.img_point, z)
        self.gtsamAssertEquals(obj1, self.obj_point)
        r1 = camera.range(self.obj_point)
        self.assertEqual(r1, r)

    def test_generic_factor(self):
        """Evaluate residual using pose and point as state variables"""
        graph = gtsam.NonlinearFactorGraph()
        state = gtsam.Values()
        measured = self.img_point
        noise_model = gtsam.noiseModel.Isotropic.Sigma(2, 1)
        pose_key, point_key = P(0), L(0)
        k = self.stereographic
        state.insert_pose3(pose_key, gtsam.Pose3())
        state.insert_point3(point_key, self.obj_point)
        factor = gtsam.GenericProjectionFactorCal3Unified(measured, noise_model, pose_key, point_key, k)
        graph.add(factor)
        score = graph.error(state)
        self.assertAlmostEqual(score, 0)

    def test_sfm_factor2(self):
        """Evaluate residual with camera, pose and point as state variables"""
        r = np.linalg.norm(self.obj_point)
        graph = gtsam.NonlinearFactorGraph()
        state = gtsam.Values()
        measured = self.img_point
        noise_model = gtsam.noiseModel.Isotropic.Sigma(2, 1)
        camera_key, pose_key, landmark_key = K(0), P(0), L(0)      
        k = self.stereographic
        state.insert_cal3unified(camera_key, k)
        state.insert_pose3(pose_key, gtsam.Pose3())
        state.insert_point3(landmark_key, self.obj_point)
        factor = gtsam.GeneralSFMFactor2Cal3Unified(measured, noise_model, pose_key, landmark_key, camera_key)
        graph.add(factor)
        score = graph.error(state)
        self.assertAlmostEqual(score, 0)

    def test_retract(self):
        expected = gtsam.Cal3Unified(100 + 2, 105 + 3, 0.0 + 4, 320 + 5, 240 + 6,
                                     1e-3 + 7, 2.0*1e-3 + 8, 3.0*1e-3 + 9, 4.0*1e-3 + 10, 0.1 + 1)
        K = gtsam.Cal3Unified(100, 105, 0.0, 320, 240,
                              1e-3, 2.0*1e-3, 3.0*1e-3, 4.0*1e-3, 0.1)
        d = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 1], order='F')
        actual = K.retract(d)
        self.gtsamAssertEquals(actual, expected)
        np.testing.assert_allclose(d, K.localCoordinates(actual))


if __name__ == "__main__":
    unittest.main()
