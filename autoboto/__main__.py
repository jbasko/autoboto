from .builder.code_generator import Autoboto


def main():
    code = Autoboto()
    code.generate_service("s3")
    code.generate_service("cloudformation")


if __name__ == "__main__":
    main()
