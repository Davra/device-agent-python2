#!/bin/bash

cd `dirname $0`

MAJ_VER=${MAJ_VER:-0}
MIN_VER=${MIN_VER:-0}
BUILD_NUMBER=${BUILD_NUMBER:-0}

# Ensure the build directory is available
if [ -d build ] ; then
	rm -rf build
fi
mkdir build

# Capture the jenkins build details for mapping back from artifact location to code
echo "${GIT_REPO}_$MAJ_VER.$MIN_VER.$BUILD_NUMBER" > build/build_jenkins.txt

# Capture the version from the library code. It is used by agents to determine if they need to download a new artifact.
grep davraAgentVersion ./davra_lib.py | cut -f 2 -d '"' > build/build_version.txt

# Assemble the artifact which is the installation bundle tar.gz
tar --exclude="build" --exclude ".git" --exclude "node_modules" --exclude="build.sh" -zcf build/davra-agent.tar.gz .

# Capture a checksum for those downloading the artifact
md5sum build/davra-agent.tar.gz > build/build_checksum.txt
