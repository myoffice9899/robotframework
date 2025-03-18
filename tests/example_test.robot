*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem

*** Variables ***
${PROFILE_DIR}    ${EMPTY}

*** Test Cases ***
Open Google
    ${PROFILE_DIR}=    Evaluate    __import__('tempfile').mkdtemp()
    Open Browser    https://www.google.com    Chrome
    ...    options=add_argument("--headless"), add_argument("--no-sandbox"), add_argument("--disable-dev-shm-usage"), add_argument("--user-data-dir=${PROFILE_DIR}")
    Sleep    5s
    Close Browser
