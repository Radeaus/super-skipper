<p align="center"><img src="https://raw.githubusercontent.com/Radeaus/super-skipper/HEAD/custom_components/super_skipper/brand/icon.png" alt="Super Skipper icon" width="96" height="96"></p>

# Super Skipper

A Home Assistant helper that watches your media players. When a keyword you choose shows up in the title or artist of what plays, it skips the track, switches to another radio station for a while, or mutes the player until the song is over.

No more ABBA on the kitchen radio. No more Christmas songs in November. No more "Advertisement" at full volume.

## How it works

You create **rules**. Each rule has keywords, one or more media players, and an action:

| Action | What happens |
| --- | --- |
| **Skip to the next track** | Calls `media_player.media_next_track`. For Spotify, Music Assistant, Sonos queues, and any other player that can skip. |
| **Switch station** | Plays a station you pick from the media browser (the **Radio Browser** source lists thousands of stations), or runs your own actions. After the time you set, Super Skipper plays what was on before. |
| **Mute until it is over** | Mutes the player while the keyword plays and unmutes once something else has played for a moment. |

Rules can be limited to moments when certain persons are (or are not) at home, and to any other condition you know from automations.

## Getting started

You need Home Assistant 2025.8 or newer.

1. **Install the integration.** Search for **Super Skipper** in the Marketplace and download it.
<!-- ha-marketplace:exclude-start -->
   Or open it in your Home Assistant directly:

   [![Open in the Marketplace of your Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Radeaus&repository=super-skipper&category=integration)

   Without the Marketplace: copy `custom_components/super_skipper` into your `custom_components` folder and restart Home Assistant.
<!-- ha-marketplace:exclude-end -->
2. **Add the helper.** Go to **Settings > Devices & services > Helpers > Create helper** and choose **Super Skipper**. You can also add it under **Integrations > Add integration**.
3. **Create a rule.** Open **Super Skipper** in the sidebar and select **Create rule**. The page asks for the keywords, the players, the action, and when the rule may act, all on one form.
4. **Repeat step 3** for every other rule. The page lists the rules with a switch to turn each one off, shows what each rule last did, and has the snooze button and the settings.

Prefer the usual dialogs? Everything on the page is also available under **Settings > Devices & services > Integrations > Super Skipper**: the three dots menu has **Create rule**, and every rule has a cog to edit it.

## Settings

### Rule: what to look for

| Field | |
| --- | --- |
| Name | Shown in the rule list and in the logbook |
| Keywords | Words or phrases to look for. Press Enter after each one |
| Media players | The rule acts on each of these players separately |
| Action | Skip, switch station, or mute |
| Match | **Whole words** (default) matches `ABBA` in `ABBA - Waterloo` but not in `Kabbalah`. **Any part of a word** matches both. **Regular expression** treats each keyword as a pattern. Case and accents never matter |
| Look in | Title and artist by default; album and channel optional. Radio stations often put the station name in the channel or artist attribute |
| Ignore station information | Texts a station shows between songs, like its name or slogan. Super Skipper then treats them as station information instead of a new track, so a mute is not lifted and a switch is not repeated |

### Rule: skip

| Field | |
| --- | --- |
| Skips in a row | After this many skipped tracks in a row the rule waits until something plays that does not match. `0` means no limit |

### Rule: switch station

| Field | |
| --- | --- |
| Station | A station from the media browser. Pick a player to browse with; the rule plays the same station on each of its players |
| Or run these actions | Your own actions instead of a station, for example a script. The variables `player` and `rule` are available |
| Return after | Minutes before Super Skipper plays what was on before. `0` keeps the new station on |
| If returning fails, play | Required when returning is on. See [Returning to what played before](#returning-to-what-played-before) |
| Or run these actions instead | Your own actions as the fallback |
| When the keyword still plays after returning | Switch again with a limit (default), switch again without limit, or switch only once |
| Switch at most | The limit for the option above |

### Rule: mute

| Field | |
| --- | --- |
| Unmute after | Seconds something else must play before the sound comes back. Covers stations that show their name between songs |
| Mute at most | Safety limit in minutes. The sound always comes back after this time |

### Rule: when the rule may act

| Field | |
| --- | --- |
| Persons | Persons whose presence decides whether the rule acts |
| The rule acts when | At least one of them is home, all of them are home, or none of them is home |
| Conditions | Any Home Assistant condition. All of them must be met |

### Integration settings

Under **Configure** on the integration:

| Option | Default | |
| --- | --- | --- |
| Snooze time | 60 minutes | How long the **Snooze** button pauses every rule |
| Cooldown between actions | 5 seconds | The least time between two actions on the same player |
| Confirmation delay | 1 second | How long a track must play before a rule acts. Filters out metadata that flickers while a player changes tracks |

## The Super Skipper page

The sidebar page is where you manage everything:

- **Rules**: the list of rules with their keywords, players and last match. The switch turns a rule off without deleting it. Select a rule to edit or delete it.
- **Create rule** opens a page with one form. The sections **Matching** and **When the rule may act** are collapsed; open them for the match mode, the attributes to search, the station information to ignore, the persons and other conditions.
- **Snooze** pauses every rule for the snooze time; **Resume** ends the pause early.
- **Settings** holds the snooze time, the cooldown and the confirmation delay.

The page needs an administrator account.

## Entities

| Entity | |
| --- | --- |
| `switch.<rule>_enabled` | Turn a rule off without deleting it. Survives restarts |
| `sensor.<rule>_last_match` | The track the rule last acted on, with the player, the action, and the time as attributes |
| `button.super_skipper_snooze` | Pause every rule for the snooze time |
| `sensor.super_skipper_snoozed_until` | When the pause ends |

Every action is written to the **logbook**, for example "No ABBA: skipped “ABBA – Dancing Queen” on Kitchen".

## Returning to what played before

Before switching, Super Skipper notes what the player plays (`media_content_id`, source and, for Sonos, a snapshot). When the time is up it plays that again and checks after ten seconds whether the player is really back. If not, it plays the fallback you chose.

This works well on Sonos, Google Cast, Squeezebox, Music Assistant and most players that report a stream URL or a `media-source://` id. It does not work when the player reports nothing that can be played again, such as Spotify queues or MusicCast inputs. That is why the fallback is required.

While the alternative station plays, Super Skipper leaves the player alone. If you start something else yourself, or turn the player off, it does not switch back.

## Known limitations

- Players only report what their integration tells Home Assistant. Spotify refreshes every 30 seconds, so a skip can take that long. Chromecast does not refresh the title of a radio stream at all.
- Some stations send "Artist - Title" in one field, or the station name as the artist. Add the station name to **Ignore station information** and keep **Look in** on title and artist.
- The Spotify media player cannot play stations from the media browser. For Spotify, use the skip action, or switch with your own actions.
- Grouped players (Sonos, Music Assistant) are controlled through the group leader only.

## Troubleshooting

- Nothing happens: check the rule's **Enabled** switch, the **Snoozed until** sensor, and the persons and conditions of the rule. Then look at the **Last match** sensor and the logbook.
- A rule skips too much: switch **Match** to whole words, or shorten the keyword list.
- A rule unmutes too early: raise **Unmute after**, or add the station's texts to **Ignore station information**.
- Turn on debug logging for `custom_components.super_skipper` to see every decision.

## Removal

Delete the rules you no longer want from the integration page, or delete the whole **Super Skipper** entry under **Settings > Devices & services**. Then remove the integration from the Marketplace. Nothing stays behind.
