# myminiprojext
It is the othello game design studio.

## Installation
To install this design studio you need to install Docker and Mongo


### Basic deployment
For a regular deployment, you need to install the following components on top of fetching this repository:
- [NodeJS](https://nodejs.org/en/) (LTS recommended)
- [MongoDB](https://www.mongodb.com/)

After all components in place, you need to install the dependencies, using `npm i` command and start your deployment 
using the `node ./app.js` command. If you have not changed the configuration, your design studio should be accessible on 
port 8888 of your localhost.

## Development
If you are using this repository as an example and would like to 'recreate' it or add further components to it, you are
going to need additional software:
- [NodeJS](https://nodejs.org/en/) (LTS recommended)
- [WebGME-CLI](https://www.npmjs.com/package/webgme-cli) (latest recommended)

You are going to use nodejs to bring in potentially new components or dependencies while the CLI is there to generate or import design studio components with handling the necessary config updates as well.


### Seed
There is a single seed in the project representing the example studio - seed1 - but all other default seeds are also available.

To create new one, just use the command `webgme new seed -f mySeedFile.webgmex mySeedName`.

### Plugin
There are four plugins in this studio
- Count - at any state of the game, the studio should be able to count how many pieces per color are on the board.
- Highlight - at each state of the game, the active player can only place their piece to specified tiles (where they would essentially initiate some color changes)
- auto - computer mechanism that can play the game, if this functionality is used, than it makes a valid move.
- undo - a function that can take the game back to the previous state, allowing the last user to make a different move.
