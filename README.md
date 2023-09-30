## Background

When it comes to music, our brain engages in complex creative processes
that involve combining elements such as rhythm, pitch, and timbre.
Today many musicians spend a significant time recording, editing, and arranging music.
This project aims to ease music generation from a sample track. The musicican can hum his melody
into his microphone, and the system will generate complementary track.

The first step in generating similar music is to analyze the style.
Style includes all elements of music. i.e rhythm, pitch and timbre.
Firstly, we detect the pitches, which helps us understand the underlying melody.
Firstly, lets define pitch.

### Musical notation

Music notation is any system used to visually represent aurally perceived music. Lets take a look at a subset of this notation which deals with pitch.

The chromatic scale is a set of twelve pitches used in music. 

$$C \;\; C\# \;\; D \;\; D\# \;\; E \;\; F \;\; F\# \;\; G \;\; G\# \;\; A \;\; A\# \;\; B$$

These notes are cyclic, therefore C comes after B. A number is used to represent the octave.
The interval between any two subsequenct notes is a semi-tone.

A4 is usually used as the reference note with frequency 440Hz. A5 is thus an octave higher (880Hz).

### MIDI

MIDI (Musical Instrument Digital Interface) is a standard interface recognized by several musical instruments and processors. In MIDI the middle C note (C4) is represented with the number 60. A note that is a semitone higher is represented by a number one higher than the previous. Similary, a note that is a semitone lower is represented by a number one less than the previous. For A4, which is 9 semitones higher than C4, the midi representation is 69.


### Mapping frequency to musical notation

We can leverage MIDI to convert frequency to musical notation.

The function to convert a frequency to MIDI number is:

$$  M(f) = 69 + 12 \cdot \log_2{\frac{x}{440}} $$


Then we can map the MIDI number to notation from the definition of MIDI.