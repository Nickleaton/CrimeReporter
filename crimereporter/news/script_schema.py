from strictyaml import Float, Int, Map, Optional, Seq, Str

SCHEMA = Map(
    {
        Optional("Source"): Str(),
        Optional("Id"): Str(),
        "Type": Str(),
        "Date": Str(),
        "Title": Str(),
        Optional("ThumbNailText"): Str(),  # Made optional for backward compatibility
        "URL": Str(),
        "Thumbnail": Str(),
        "Location": Str(),
        "Tags": Seq(Str()),
        "Description": Str(),
        Optional("People"): Seq(
            Map(
                {
                    "Person": Map(
                        {
                            "Name": Str(),
                            "Nationality": Str(),
                            Optional("Age"): Float(),
                            Optional("DateOfBirth"): Str(),
                            "Gender": Str(),
                            "Role": Str(),
                            Optional("Image"): Str(),
                            Optional("Crimes"): Seq(Map({"Crime": Map({"Offence": Str(), "Sentence": Str()})})),
                        }
                    )
                }
            )
        ),
        Optional("Images"): Map(
            {
                "Combine": Map(
                    {
                        "Target": Str(),
                        "Horizontal": Int(),
                        "Vertical": Int(),
                        "Sources": Seq(Str()),
                    }
                )
            }
        ),
        "Segments": Seq(
            Map(
                {
                    "Segment": Map(
                        {
                            Optional("Image"): Str(),
                            Optional("Text"): Str(),
                            Optional("Video"): Str(),
                            Optional("Audio"): Str(),
                        }
                    )
                }
            )
        ),
    }
)
