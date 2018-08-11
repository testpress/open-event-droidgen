import json
import os
import re
import shutil
import subprocess
import urllib
import uuid

import requests
import validators
from celery.utils.log import get_task_logger
from flask import current_app
from git import Repo

from app.utils import clear_dir, get_build_tools_version
from app.utils.assets import create_various_density_images
from app.utils.libs.asset_resizer import DENSITY_TYPES
from app.utils.notification import Notification

logger = get_task_logger(__name__)

def ignore_files(path, names):
    logger.info('Working in %s' % path)

    # Ignore build/generated folder
    return ("build", ".gradle", ".idea")

class Generator:
    """
    The app generator. This is where it all begins :)
    """

    def __init__(self, config, via_api=False, identifier=None, task_handle=None, build_type=None, theme_colors=None):
        print "generator init0"
        if not identifier:
            self.identifier = str(uuid.uuid4())
        else:
            self.identifier = identifier
        self.task_handle = task_handle
        self.update_status('Starting the generator')
        self.config = config
        self.working_dir = config['WORKING_DIR']
        self.src_dir = config['APP_SOURCE_DIR']
        self.creator_email = ''
        self.is_auth_enabled = False
        self.event_name = ''
        self.app_name = ''
        self.app_working_dir = os.path.abspath(self.working_dir + '/' + self.identifier + '/android-src/')
        self.app_temp_assets = os.path.abspath(self.working_dir + '/' + self.identifier + '/assets-src/')
        self.api_link = ''
        self.apk_path = ''
        self.via_api = via_api
        self.build_type = build_type
        self.theme_colors = theme_colors
        self.app_launcher_icon = None
        self.notification_icon = None
        self.login_screen_image = None
        self.splash_screen_image = None
        self.splash_screen_image_land = None
        self.splash_screen_image_large = None
        self.splash_screen_image_large_land = None
        self.google_services_json = None
        self.config_json = None

    def get_path(self, relative_path):
        """
        Get the path to a resource relative to the app source
        :param relative_path:
        :return:
        """
        return os.path.abspath(self.app_working_dir + '/' + relative_path)

    def get_temp_asset_path(self, relative_path):
        """
        Get the path to a resource relative to the temp assets dir
        :param relative_path:
        :return:
        """
        return os.path.abspath(self.app_temp_assets + '/' + relative_path)

    def normalize(self, creator_email, endpoint_url=None, is_auth_enabled=False, config_file=None, zip_file=None):
        """
        Normalize the required data irrespective of the source
        :param creator_email:
        :param is_auth_enabled:
        :param endpoint_url:
        :param zip_file:
        :return:
        """

        self.update_status('Normalizing source data')
        if not endpoint_url and not zip_file:
            raise Exception('endpoint_url or zip_file is required')
        if endpoint_url:
            os.makedirs(self.app_temp_assets)
            app_details = requests.get(endpoint_url).json()
            self.download_event_data()
        else:
            jsonFile = open(config_file, "r")
            app_details = json.load(jsonFile)

        os.makedirs(self.app_temp_assets)

        self.creator_email = creator_email
        self.config_json = config_file
        self.google_services_json = zip_file

        self.update_status('Processing images')

        login_screen_image = app_details['login_screen_image']
        splash_screen_image = app_details['splash_screen_image']
        splash_screen_image_land = app_details['splash_screen_image_land']
        splash_screen_image_large = app_details['splash_screen_image_large']
        splash_screen_image_large_land = app_details['splash_screen_image_large_land']
        launcher_icon = app_details['launcher_icon']
        notification_icon = app_details['notification_icon']

        if validators.url(login_screen_image):
            self.login_screen_image = self.get_temp_asset_path('logo.png')
            urllib.urlretrieve(login_screen_image, self.login_screen_image)

        if validators.url(splash_screen_image):
            self.splash_screen_image = self.get_temp_asset_path('splash_screen.png')
            urllib.urlretrieve(splash_screen_image, self.splash_screen_image)

        if validators.url(splash_screen_image_land):
            self.splash_screen_image_land = self.get_temp_asset_path('splash_screen_land.png')
            urllib.urlretrieve(splash_screen_image_land, self.splash_screen_image_land)

        if validators.url(splash_screen_image_large):
            self.splash_screen_image_large = self.get_temp_asset_path('splash_screen_large.png')
            urllib.urlretrieve(splash_screen_image_large, self.splash_screen_image_large)

        if validators.url(splash_screen_image_large_land):
            self.splash_screen_image_large_land = self.get_temp_asset_path('splash_screen_large_land.png')
            urllib.urlretrieve(splash_screen_image_large_land, self.splash_screen_image_large_land)

        if validators.url(launcher_icon):
            self.app_launcher_icon = self.get_temp_asset_path('icon.png')
            urllib.urlretrieve(launcher_icon, self.app_launcher_icon)

        if validators.url(notification_icon):
            self.notification_icon = self.get_temp_asset_path('ic_notification.png')
            urllib.urlretrieve(launcher_icon, self.notification_icon)

    def generate(self, should_notify=True):
        """
        Generate the app
        :return: the path to the generated apk
        """

        logger.info('Working directory: %s' % self.app_working_dir)

        self.update_status('Preparing parent source code')

        self.prepare_source()

        self.update_status('Generating app configuration')

        shutil.copyfile(self.config_json, self.app_working_dir + '/app/src/main/assets/config.json')

        with open(self.google_services_json, "r") as infile:
            with open(self.app_working_dir + '/app/google-services.json', 'w') as outfile:
                shutil.copyfileobj(infile, outfile)

        self.update_status('Generating various density images')

        create_various_density_images(self.app_launcher_icon, self.app_working_dir)
        create_various_density_images(self.notification_icon, self.app_working_dir)
        shutil.copyfile(self.login_screen_image, self.app_working_dir + '/app/src/main/res/drawable/logo.png')
        shutil.copyfile(self.splash_screen_image, self.app_working_dir + '/app/src/main/res/drawable/splash_screen.png')
        shutil.copyfile(self.splash_screen_image_land, self.app_working_dir + '/app/src/main/res/drawable-land/splash_screen.png')
        shutil.copyfile(self.splash_screen_image_large, self.app_working_dir + '/app/src/main/res/drawable-large/splash_screen.png')
        shutil.copyfile(self.splash_screen_image_large_land, self.app_working_dir + '/app/src/main/res/drawable-large-land/splash_screen.png')

        self.update_status('Preparing android build tools')

        build_tools_version = get_build_tools_version(self.get_path('app/build.gradle'))

        logger.info('Detected build tools version: %s' % build_tools_version)

        build_tools_path = os.path.abspath(os.environ.get('ANDROID_HOME') + '/build-tools/' + build_tools_version)

        logger.info('Detected build tools path: %s' % build_tools_path)

        self.update_status('Building android application package')

        self.run_command([os.path.abspath(self.config['BASE_DIR'] + '/scripts/build_apk.sh'), build_tools_path, self.build_type])

        self.update_status('Application package generated')

        self.apk_path = self.get_path('release.apk')

        logger.info('Generated apk path: %s' % self.apk_path)

        if should_notify:
            self.notify()

        apk_url = '/static/releases/%s.apk' % self.identifier

        logger.info('Final apk download path: %s' % apk_url)

        shutil.move(self.apk_path, os.path.abspath(self.config['BASE_DIR'] + '/app/' + apk_url))

        self.update_status('SUCCESS', message=apk_url)

        self.cleanup()

        return apk_url

    def download_event_data(self):
        """
        Download all event data from api i.e. event, speakers, sessions etc..
        :return:
        """
        logger.info('Downloading event data')
        self.save_file_in_temp_assets('event')
        self.save_file_in_temp_assets('microlocations')
        self.save_file_in_temp_assets('sessions')
        self.save_file_in_temp_assets('speakers')
        self.save_file_in_temp_assets('sponsors')
        self.save_file_in_temp_assets('tracks')
        self.save_file_in_temp_assets('sessions/types')
        logger.info('Download complete')

    def save_file_in_temp_assets(self, end_point='event'):
        """
        Save response from specified end_point in temp assets directory
        :param end_point:
        :return:
        """
        if self.api_link:
            response = requests.get(self.api_link + '/' + end_point)
            file = open(self.get_temp_asset_path(end_point), "w+")
            file.write(response.text)
            file.close()
            logger.info('%s file saved', end_point)

    def prepare_source(self):
        """
        Prepare the app-specific source based off the parent
        :return:
        """
        # shutil.copytree(self.src_dir, self.app_working_dir)
        Repo.clone_from("https://github.com/testpress/android.git", self.app_working_dir)
        for density in DENSITY_TYPES:
            mipmap_dir = self.get_path("app/src/main/res/mipmap-%s" % density)
            if os.path.exists(mipmap_dir):
                shutil.rmtree(mipmap_dir, True)
        clear_dir(self.get_path("app/src/main/assets/"))

    def cleanup(self):
        """
        Clean-up after done like a good fella :)
        :return:
        """
        logger.info('Cleaning up %s' % self.working_dir)
        shutil.rmtree(os.path.abspath(self.working_dir + '/' + self.identifier + '/'))
        zip_file = os.path.join(self.config['UPLOAD_DIR'], self.identifier)
        if os.path.isfile(zip_file):
            os.remove(zip_file)

    def notify(self, completed=True, apk_path=None, error=None):
        """
        Notify the creator of success or failure of the app generation
        :param completed:
        :param apk_path:
        :param error:
        :return:
        """
        if completed and apk_path and not error:
            Notification.send(
                to=self.creator_email,
                subject='Your android application for %s has been generated ' % self.event_name,
                message='Hi,<br><br>'
                        'Your android application for the \'%s\' event has been generated. '
                        'And apk file has been attached along with this email.<br><br>'
                        'Thanks,<br>'
                        'Open Event App Generator' % self.event_name,
                file_attachment=apk_path,
                via_api=self.via_api
            )
        else:
            Notification.send(
                to=self.creator_email,
                subject='Your android application for %s could not generated ' % self.event_name,
                message='Hi,<br><br> '
                        'Your android application for the \'%s\' event could not generated. '
                        'The error message has been provided below.<br><br>'
                        '<code>%s</code><br><br>'
                        'Thanks,<br>'
                        'Open Event App Generator' % (self.event_name, str(error) if error else ''),
                file_attachment=apk_path,
                via_api=self.via_api
            )

    def update_status(self, state, exception=None, message=None, skip_log=False):
        if not skip_log:
            logger.info(state)
        if self.task_handle:
            if not current_app.config.get('CELERY_ALWAYS_EAGER'):
                meta = {}
                if exception:
                    meta = {'exc': exception}
                if message:
                    meta = {'message': message}
                self.task_handle.update_state(
                    state=state, meta=meta
                )

    def run_command(self, command):
        logger.info('Running command: %s', command)
        process = subprocess.Popen(command,
                                   stdout=subprocess.PIPE,
                                   cwd=self.app_working_dir,
                                   env=os.environ.copy())
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info('> %s', output)
                self.generate_status_updates(output.strip())
        rc = process.poll()
        return rc

    def generate_status_updates(self, output_line):
        if 'Starting process \'Gradle build daemon\'' in output_line:
            self.update_status('Starting gradle builder', skip_log=True)
        elif 'Creating configuration' in output_line:
            self.update_status('Creating configuration', skip_log=True)
        elif 'Parsing the SDK' in output_line:
            self.update_status('Preparing Android SDK', skip_log=True)
        elif 'app:preBuild' in output_line:
            self.update_status('Running pre-build tasks', skip_log=True)
        elif 'Loading library manifest' in output_line:
            self.update_status('Loading libraries', skip_log=True)
        elif 'Merging' in output_line:
            self.update_status('Merging resources', skip_log=True)
        elif 'intermediates' in output_line:
            self.update_status('Generating intermediates', skip_log=True)
        elif 'is not translated' in output_line:
            self.update_status('Processing strings', skip_log=True)
        elif 'generateFdroidReleaseAssets' in output_line:
            self.update_status('Processing strings', skip_log=True)
        elif 'Adding PreDexTask' in output_line:
            self.update_status('Adding pre dex tasks', skip_log=True)
        elif 'Dexing' in output_line:
            self.update_status('Dexing classes', skip_log=True)
        elif 'packageGoogleplayRelease' in output_line:
            self.update_status('Packaging release', skip_log=True)
        elif 'assembleRelease' in output_line:
            self.update_status('Assembling release', skip_log=True)
        elif 'BUILD SUCCESSFUL' in output_line:
            self.update_status('Build successful. Starting the signing process.', skip_log=True)
        elif 'signing' in output_line:
            self.update_status('Signing the package.', skip_log=True)
        elif 'jar signed' in output_line:
            self.update_status('Package signed.', skip_log=True)
        elif 'zipaligning' in output_line:
            self.update_status('Verifying the package.', skip_log=True)
        elif 'Verification successful' in output_line:
            self.update_status('Package verified.', skip_log=True)
        elif output_line == 'done':
            self.update_status('Application has been generated. Please wait.', skip_log=True)
