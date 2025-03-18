*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${BROWSER}    chrome

*** Test Cases ***
Open Google
    Open Browser    https://www.google.com    ${BROWSER}
    Sleep    2s
    Capture Page Screenshot
    Close Browser
