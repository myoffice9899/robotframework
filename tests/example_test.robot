*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem

*** Variables ***
${PROFILE_DIR}    ${EMPTY}

*** Test Cases ***
Open Google
    ${PROFILE_DIR}=    Evaluate    __import__('tempfile').mkdtemp()
    Open Browser    https://www.google.com    Chrome
    ...    options=--headless --no-sandbox --disable-dev-shm-usage --user-data-dir=${PROFILE_DIR}
    Sleep    5s
    Close Browser
