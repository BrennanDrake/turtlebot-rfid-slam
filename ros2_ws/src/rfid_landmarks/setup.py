from setuptools import setup

package_name = 'rfid_landmarks'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Brennan Drake',
    maintainer_email='81040749+BrennanDrake@users.noreply.github.com',
    description='RFID landmark mapping and Nav2 covariance replanning.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'rfid_landmark_manager = rfid_landmarks.landmark_manager:main',
            'covariance_replan_node = rfid_landmarks.covariance_replan:main',
        ],
    },
)
