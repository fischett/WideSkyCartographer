# Identify Stars in Wide-Angle Images with Crop-Wise Resolution
## Locate stars and pinpoint their positions in your wide-angle sky images with this Python program!

This tool leverages the power of nova.astrometry.net and the `Client.py` service from the "astrometry.net" repository (created by "dstndstn/astrometry.net" ([https://github.com/dstndstn/astrometry.net](https://github.com/dstndstn/astrometry.net))).

### Key Features:
* Wide-Angle Support: Conquer those panoramic images by intelligently cropping them into smaller regions perfect for nova.astrometry.net.
* Batch Processing: Tackle single images or entire folders of PNG, JPG, and FITS files (FITS support currently under testing).
* Detailed Output: Dive into per-image results with:
  * Original image copy.
  * Overlaid image highlighting identified stars (brighter to fainter).
  * Text file detailing object data (coordinates, variance, magnitude).
  * Comprehensive folder with cropped regions, sent data, filtered coordinates, and more.
  * Visualized cropped regions overlaid on the original image.

### Get Started:
* Secure your API access: Create a free account at nova.astrometry.net and obtain your personal API password. 
* Clone this repository: Grab the code from GitHub and install the required libraries.
* Run the program: Enter your API password when prompted.
* Choose your files: Select single images or entire folders for processing.
* Explore the results: Each image gets its own dedicated folder showcasing the analysis.

### Important Notes:
* FITS format support is still undergoing testing.



## Acknowledgements and Modifications

This project builds upon the valuable foundation of the "astrometry.net" repository, originally authored by "dstndstn/astrometry.net" ([https://github.com/dstndstn/astrometry.net](https://github.com/dstndstn/astrometry.net)). I sincerely appreciate their contributions and encourage all users to explore the original project, its documentation, and the dedication of the original team.

**Copyright:**

The mentioned original repository code used in this project is subject to the following licenses:

* Parts written by the Astrometry.net Team are licensed under a 3-clause BSD-style license.
* However, due to the inclusion of libraries licensed under the GNU General Public License (GPL), the entire work is distributed under the GPL version 3 or later. 

**Modifications:**

I have made specific modifications to the following files in the original repository:

* `client.py` (here presented as `client_OriginalFrom_astronomy-net.py`, being `'Client.py'` the modified version): 
1- The print statements in the modified file (`Client.py`) have mostly been commented out, so there will be less output when running it.
2- There is a new optional argument added in _get_upload_args in `Client.py`: use_sextractor. This allows specifying whether to use SExtractor for source extraction.
3- The sub_status method in `Client.py` returns the full result dictionary, not just the status.
4- The annotate_data method is new in Client.py. It retrieves the annotation data for a given job ID.
5- The jobs_by_tag method in `Client.py` takes an additional "exact" parameter to control whether an exact tag match is required.
6- Some minor code formatting changes like spacing around operators.
Other than that the core functionality is the same. The changes mainly add some optional new parameters and retrieve additional data from the API.


**Transparency and Responsible Use:**

I believe in open collaboration, responsible use of existing code, and fostering a thriving community around astronomical software development. By acknowledging the original authors, sharing my modifications with clear explanations, and choosing a compatible license, I aim to contribute meaningfully to the advancement of these tools while upholding intellectual property rights.

**Additional Notes:**

* Feel free to contact me if you have any questions, feedback, or suggestions regarding the modifications made in this project.
* If you find my work helpful, consider contributing back to the original "astrometry.net" project or creating your own derivative projects with appropriate licensing. By doing so, we can collectively accelerate progress and enhance the available resources for the benefit of the entire astronomical community.


**I hope this section effectively acknowledges the original authors, clarifies my modifications, and promotes transparency and responsible use.**
